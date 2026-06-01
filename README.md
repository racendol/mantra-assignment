# Judge API

## Initial Setup

```
uv sync --all-groups

uv run manage.py migrate
```

### Run tests

```
uv run poe test
```

### Run server

```
uv run manage.py runserver
```

### Lint and format code

```
uv run poe lint
uv run poe format
```

# Evaluation
## 1. Explanation
### /judge logic
For this assignment, we need to check if `sentence1` and `sentence2` have entailment or not. This is a classic NLP task called Natural Language Inference (NLI). NLI takes 2 arguments — premise and hypothesis — and classifies whether they are entailment, contradiction, or neutral. Because it's a classic classification problem that takes input and produces an output, there are many ways to solve it.

One of the most common ways to solve a classification problem is by using machine learning models. This is especially true for NLI, because finding entailment is hard with classic ML algorithms like random forest — the words involved in entailment can be very contradictory or seemingly unrelated, and we need to find the entailment from deep semantic relations. Technically, we could build a neural network from scratch and train it, but implementing a transformer or BERT from scratch would take too much time. Because of that, I chose to use a pretrained neural network model to save time.

Since language library models are allowed, I use the Sentence-Transformers library for this assignment. Specifically, I use the CrossEncoder model because it's designed for classification tasks. I use a pretrained model trained to solve NLI tasks (https://sbert.net/docs/cross_encoder/pretrained_models.html#nli). The model I use is `MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli` (https://huggingface.co/MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli). I chose this because the assignment description includes Japanese input, so I need a model that can handle multilingual input. Also, since this is just a mini-project, we don't need a large model — the smallest size is sufficient.

When we call `.predict()` on the model, it outputs 3 values in this order: `[entailment, neutral, contradiction]`, as specified in the model description. The values are in logits, so we convert them to a 0–100 range using softmax to get a clean score. Since this task only needs 2 labels (entailment and not entailment) I combine the neutral and contradiction scores to create the not entailment label. With this setup, the judge API works as specified.

### Rate Limit
Besides the core `/judge` API, there's also a rate limit requirement. For the rate limit algorithm, I use the fixed window algorithm. This algorithm stores the timestamp of the 1st request, then increments a counter until it reaches the max limit, at which point it returns a `RateLimitExceeded` error. When a request comes in after the time window has passed, the counter resets and the request is allowed again.

I chose the fixed window algorithm because it's straightforward to implement, and since the idempotency key is just `client_ip`, we only need 1 row per IP, which is easy to track — especially during the concurrency tests required for this assignment. The DB also won't grow very fast as long as we control the IPs used for testing.

However, the fixed window algorithm does have a weakness. Because it resets to 0 after the time window expires, a user can technically abuse it and send almost double the limit at the window boundary. For example, with a rate limit of 5 and a time window of 1s, a user could send 1 request at `t: 00:00:00`, then 4 more at `00:00:59`, then 5 more at `00:01:01` — effectively sending 10 requests within ~1 second. This allows spike requests that can bypass the intended limit. That said, over a longer period it will average out to the specified rate (5 req/s), so as long as we can handle the spike, it's not a critical problem — and the spike is at most 2x the limit.

A better algorithm for this is the sliding window. With sliding window, we set the start of the window to the earliest recorded request timestamp, store the timestamp of each request, and recalculate the window start on every new request. If the number of requests within the window exceeds the rate limit, we return `RateLimitExceeded`; otherwise the request is accepted and its timestamp is stored for future window calculations. Because the window is dynamically calculated based on actual request timestamps, the spike problem is eliminated and the limit becomes a "true" rate limit.

The reason I didn't use the sliding window is because it requires storing all request data (IP and timestamp) for every successful request, which causes the DB to grow fast and requires a cleanup strategy for stale data. It's also harder to reason about during concurrency testing. Finally, its time complexity is O(N) for N = rate limit, whereas fixed window is O(1). Since the assignment doesn't specify a need for a "true" rate limit, I decided fixed window is sufficient for the requirements.

### Project Structure
Not directly related to the 2 main problems, but worth addressing. For this project, I tried to code it as "corporate-like" as possible for the sake of clean code and readability — even though it's honestly overkill and over-engineered for these requirements. I coded it this way to be as safe as possible and aim for production-level quality. This is also the first time I've written Python/Django code like this, since I usually use Python for small hobby projects, and the last time I built something in Python was in university (technically I also worked professionally on a Python project at Samsung, but it was mostly maintaining legacy Python 2 code). So it was a refreshing experience.

## 2. Explanation of how judgment criteria meets requirements F1-F3
### F1
For the `/judge` API, I built `JudgeViewSet` and registered it at `/api/v1/judge`. I added the `/api/v1/` prefix for clean API versioning. Since the requirements don't strictly specify `/judge` but do mention API design, I tried to follow best practices and keep it extendable.

The API accepts `sentence1` and `sentence2` as input, as defined in `JudgeResultSerializers`. `sentence1` is used as the premise and `sentence2` as the hypothesis for the entailment model. For the entailment layer, I created `EntailmentService`, which runs prediction using the pretrained model I described earlier. The model outputs 3 values, which are then processed into entailment and not entailment labels as explained above. The model uses a lazy-loading singleton that loads on the first request, with locking to ensure it's only loaded once.

After getting the label and score from `EntailmentService`, the ViewSet returns them according to the requirements. With this, the `/judge` API satisfies the F1 requirements.

### F2
For the `/judge/bulk` API, I added a new method to `JudgeViewSet`. The input uses the same `JudgeResultSerializers`, but with `many=True`, which allows it to accept an array of inputs, for example:

```
[
    {
    "sentence1": "A man is riding a bicycle",
    "sentence2": "A person is outdoors"
    },
    {
    "sentence1": "The sky is blue",
    "sentence2": "It is raining"
    }
]
```

The view then passes the input as a list to `EntailmentService`. Note that `EntailmentService` already accepts premise and hypothesis as lists, so no changes were needed there. The CrossEncoder model also natively accepts batched input — in fact, batching is more efficient than predicting one by one since the model is optimized for it. The output is returned as an array, for example:

```
[{"label":"NO_ENTAIL","score":0.9898723363876343},{"label":"NO_ENTAIL","score":0.8235358595848083}]
```

Returning the output as an array also just requires adding `many=True` to `JudgeResultSerializers`, so no additional logic changes were needed.

Since the requirements mention `up to 100 pairs`, I added a 100-pair limit in the serializer, which returns a `ValidationError` and a 400 response when the limit is exceeded.

With this, the `/judge/bulk` API satisfies the F2 requirements.

### F3
For the rate limit logic, it's as explained earlier. The rate limit is implemented in `RateLimitThrottle` using DRF's Throttle feature. The IP is acquired using the built-in `get_ident(request)`. When a `RateLimitExceeded` exception occurs, it's caught and re-raised as a `Throttled` exception, which is then caught by `custom_exception_handler` to return a 429 Too Many Requests response.

For each incoming request, the IP is recorded as a `RequestLog` entry in the DB, storing `created_at` and `counter`. For subsequent requests within the time window, the counter increments until it exceeds the limit, at which point `RateLimitExceeded` is raised. When a request comes in after the time window has passed, the counter resets and the request proceeds normally.

With this, the rate limit is working and satisfies the F3 requirements.

### Non functional requirements
## Latency
There are 2 main bottlenecks for latency:
1. 1st request latency (lazy load)
2. Model prediction latency

### 1. 1st request latency (lazy load)
Because I use lazy loading, the first request will have noticeably higher latency since it triggers the model to load. The fix would be to switch to eager loading or to warm up the model after startup before the first request comes in. Since there's no latency requirement in the assignment and time was limited, I kept lazy loading. It also reduces startup time, especially during testing, so the tradeoff is worth it for this assignment.

### 2. Model prediction latency
We use a small model, which gives faster inference at the cost of some accuracy compared to larger models. We could reduce latency further by using a simpler ML algorithm, but that would hurt performance significantly. Conversely, using a larger model would improve accuracy but slow down inference considerably. In my opinion, using a mini/small transformer model gives the best balance of accuracy and latency for this use case.

## Concurrent writes
For concurrent writes, I use row-level locking when writing to the DB using PostgreSQL. I use `select_for_update` to lock the row so concurrent writes to the same IP don't result in duplicate entries. Initially I used SQLite with manual locking at the Python layer, but SQLite uses DB-level locking, which caused frequent locking errors during stress testing. Because of that, I switched to PostgreSQL. The concurrency tests in `test_concurrency` verify that concurrent writes work correctly with no duplicates — particularly `test_30_ips_concurrent_writes`, which tests at least 30 concurrent DB writes.

## Maintain request logs
For every request logs, I logged the request details using RequestLoggingMiddleware. This will log all the incoming request. And then I configured the logger settings to save it in logs/app.log. Since there's no log rotation requirement, I kept it as simple file logging.

## 3. 3 ideas for future accuracy improvements
### 1. Microservices
The first idea is to adopt a microservices architecture — specifically, separating the `EntailmentService` layer into its own service. This would decouple the API layer from the model-serving layer, allowing them to scale independently based on their respective workloads. For example, the API service may need to handle a large number of lightweight requests, while the inference service may require GPU resources or larger compute instances.

This separation also simplifies model deployment and lifecycle management. New models can be rolled out, A/B tested, or upgraded without impacting the API layer. In addition, a dedicated inference service makes it easier to support larger models, model ensembles, or specialized hardware accelerators in the future.

### 2. Better rate limiting logic
The current rate limiting uses fixed window, which has the burst-request weakness described earlier. This can be improved by switching to a sliding window algorithm, which provides smoother traffic control and better protection against burst request.

Additionally, the current rate limit state is stored in PostgreSQL. For rate limiting specifically, an in-memory DB like Redis would be a better fit since the data is short-lived and frequently updated. This would reduce database load, improve throughput, and enable distributed rate limiting across multiple application instances.

### 3. Improve the model
Currently we only use the pretrained weights of the small model version. Prediction quality could be improved in several ways.

First, we can use larger and better model to improve the accuracy. A much larger and better model can have better accuracy performance, but will comes at the inference performance costs.

Second, the model could be fine-tuned on domain-specific data. This will allow it to have better performance according to the target use case. We can also monitor and periodically retrain/fine tune the model so the model will have better accuracy over time.

# Automated tests (pytest)
The automated tests are in the `tests` folder within each package, and can be run with `uv run poe test`.

# API documentation (OpenAPI YAML or Markdown tables, etc.)
The API documentation is in `openapi.yaml`, generated using the `spectacular` package.

# Other documentation
Since I use Sentence-Transformers, the model is around 500 MB to download, not technically a "large" language model by today's standards, but still a considerable size. Caching is handled automatically by the Sentence-Transformers package, which caches the model to disk after the first download.

Also, since I use a pretrained model, I'm not entirely sure what the `stats accuracy calculation` requirement in pytest means since we're using the pretrained model as-is without any training. In my opinion, testing model accuracy isn't necessary here since we're not training anything ourselves.