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
For this assignment, we need to check if sentence1 and sentence2 have entailment or not. This is a classic NLP task, named Natural Language Inference (NLI). NLI is a task that required 2 arguments: premise and hypothesis, then it will classify if premise and hypothesis are classified as entailment, contradiction, or neutral. Or, NLI is a classification problem. Because it's a classic classification problem that takes input and prints an output, we have many ways to solve it.

One of the most common way to solve classification problem is by using machine learning models. This is especially true for NLI problem, because finding entailment is hard if we use the more classic machine learning algorithm for classification such as random forest, because the word for entailment can be very contradictive or not related and we must find the entailment from deep semmantic relation of the word. Technically, we can create neural network from scratch and train it, but really implementing transformer or BERT from scratch will waste so much time. So because of that, i choose to use pretrained neural network model to cut time.

Because language library models are allowed, for this assignment I use a Sentence-Transformers library. I specifically use the CrossEncoder model because it's the model that are used for classification task. I use pretrained models that are trained to solve NLI task (https://sbert.net/docs/cross_encoder/pretrained_models.html#nli). For this task I use model this model: `MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli` (https://huggingface.co/MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli). The reason I choose this is because in the assignment description it has Japanese input, so I need a model that can handle multilanguage input. Also because it's just a mini-project, we don't need a large model and only need the smallest size model.

When we use the model using .predict() function, it will output 3 values, which are in order are values of: [entailment, neutral, contradiction]. These are specified in the model description. The values are also on logits, so we must convert it to 0-100 using softmax function, so we get nice looking score/prediction value. Also, because on this task we only need 2 label: entailment and not entailment, I combine the score of neutral and contradiction to create not entailment label. With this configuration, we can create the judgement API to work as the specification.

### rate limit
Besides the core /judge API, there's also one more task for this assignment: rate limit. For rate limit algorithm, I use the fixed window algorithm. This algorithm will store the 1st time the request are coming, and then will increase the counter until it reach max limit of the rate, which then will return the RateLimitExceeded error. When a request exceed the 1st time along the specified time window, it will then reset the counter so the request can be allowed again.

The reason why I choose the fixed window algorithm is because it's easy to implement, and because the idempotency key is just client_ip we only need to create 1 row per IP so it's easy to track, especially when during concurrency test that are required for this assignment, and also the DB won't grow very fast as long as I control the IP to test.

But, the fixed window algorithm have weakness too. Because it automatically reset to 0 after exceeding time limit, technically the user can abuse it and have almost double the limit at border time. For example, with rate limit 5 and time window 1s, the user request 1 time at t: 00:00:00, then at 00:00:59 the user can request 4 times, then at 00:01:01 request 5 times, making the user technically sent 10 request at ~1 second. This make it the user can have spike requests to avoiding the limit. Nevertheless, at long time it will be averaged at the specified rate limit and time window (5 req/s) because of the algorithm, so as long as we can handle the spike it's not a big breaking problem, and even then the spike is at most 2x the limit.

The better algorithm for this is the sliding window. With sliding window we calculate the start of the window as the earliest time the request created, and then counter the incoming request and storing the timestamp of each request. Everytime new request is coming, we recalculate the earliest time for the start of the window. And then if there's more data than the specified rate limit at the specified time window, it will return RateLimitExceeded, and if not, then the request is inserted, to be calculated for the future start of the window. Because the rate limit window is dynamically set according to the timestamp of each data, the spike problem that i mentioned earlier is fixed and it the incoming request will be "true" limit of 5 req/s.

But, the reason i don't use the sliding window is because we need to store all of the data (IP and timestamp) for each request that are sucessfully coming. Because of this, the data on DB can grow very fast and we need to implement something or find way to delete all the "stale" data that are not used. Also because of this, it's harder to track on concurrency test if there're no duplicate write or not. And the final reason it's because it will be slower because the time complexity is O(N), for N = rate limit, while the fixed window algorithm is just O(1). Because the assignment doesn't specify if we need to implement "true" rate limit, I decided that the fixed window algorithm is fine and satisfy the requirement.

### project structure
Not really explanation of the main 2 problem, but i think needs some addressing. For this project, because of the evaluation of clean code and readability, i tried to code it as "corporate-like" as possible, even though it's honestly overkill and overengineer for this requirements. Nevertheless, I tried to code it like this because of the evaluation so I tried to be as safe as possible and tried to code it like production-like level as possible. This is also first time I write python/django code like this because I usually use python for small hobby project and the last time I built something on python is on University (technically I also worked professionally on a Python project on Samsung, but it's mostly maintining legacy Python2 code), so it's also refreshing experience to me.

## 2. Explanation of how judgment criteria meets requirements F1-F3
### F1
For /judge API, I built the JudgeViewSet and set it on /api/v1/judge. I set prefix /api/v1/ for clean API versioning, and because in the requirements it doesn't say strict `/judge` while also mentioning API design requirement, I tried to be as extendable and follows the best practice as possible. 

On this API I accept input sentence1 and sentence2 as specified in JudgeResultSerializers. sentence1 will be the premise, and sentence2 will be the hypothesis input for the entailment judge model layer. For entailment  layer, I create the EntailmentService that will predict using the machine learning model that I explained before. With the premise and hypothesis input, the pretrained model will predict and outputs 3 values, then are processed to entailment and not entailment output as explained before. For the model, i use lazy loading singleton that will load the model on 1st request on startup. I also add locking to make sure the 1st load is only load 1 time only.

After getting the label and score from the EntailmentService, then the ViewSet will return the label and the score, according to the requirements. And so, because of that, the /judge API satisfy the F1 requirements.

### F2
For /judge/bulk API, I built it on a new method on JudgeViewSet. Specifically for bulk, the input are the same (JudgeResultSerializers), but now with option many=true. This will make it accept input in array, example:

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

After that, on the view method it will process the input as list to the entailmentservice. Note that the entailmentservice already accepts input the promise and hypothesis as list, so there's no change needed. Also, the model for prediction also accept the lists as batch. in fact, it's way more efficient to predict batches of input instead of doing for loop and doing predict 1 by 1, because the CrossEncoder model is optimized to take batch of input. After that, we return the output as array, example::

```
[{"label":"NO_ENTAIL","score":0.9898723363876343},{"label":"NO_ENTAIL","score":0.8235358595848083}]
```
To return output as array, we also just need to add many=true on the JudgeResultSerializers, so there's no need to change code logic.

Also, in the requirements, it says `up to 100 pairs`, so for this I make a 100 pair limit on the serializer, and will return ValidationError and then 400 error when it gets input that are above the pair limit.

So with these the /judge/bulk API satisfy the F2 requirements.

### F3
For rate limit logic, it's as I explained before. The rate limit is in RateLimitThrottle, using the Throttle feature from Django REST Framework. The IP are acquired using the built in get_ident(request). When RateLimitExceeded exception happens, it will catch that and return Throttle exception which then catched on custom_exception_handler to return the 429 too many request error.

For each incoming request the IP will be recorded as RequestLog data on DB, that will store the created_at and counter.  Then for next incoming request that are still in time window, it will increment the counter until the counter is above limit, which then it will return RateLimitExceeded exception. When the request have time that are longer than the time window, it will reset the counter instead and forward the request as normal. 

So with these, the rate limit function is working and satify the F3 requirements.

### Non functional requirements
## latency
There're 2 main bottleneck for latency in this:
1. 1st request (lazy load) request latency
2. model predict latency

### 1. 1st request (lazy load) request latency
Because I use lazy loading, on the 1st request there will be latency on the 1st request because it will try to load the model on 1st request. Because of that, the 1st request will be considerably have large latency. The fix to this is either to change it to eager-loading or warm up/loading after some time after startup before 1st request. But because there's no requirement latency and do not have time, I only applied lazy-loading. Using lazy loading also reduce startup time especially when testing so for this assignment it's worth the tradeoff.

### 2. model predict latency
For this model, we only use a small model, so it have faster inference performance, but at the cost of worse accuracy performance than larger model. Of course, we can reduce latency by using simpler machine learning model/algorithm instead of transformers, but the performance will also hurts a lot. The opposite is also true, where we can increase the accuracy performance by using larger model, but the inference performance will be much slower. In my opinion, using mini/small transformers model for this have the best balance of accuracy and latency.

## concurrent writes
For concurrent writes, I make sure there's row-level locking when writing to DB using PostgreSQL. I use select_for_update to lock the row so when updating multiple IP it doesn't do duplicate write. Short story, at first I use SQLite with manual locking in the Python layer, but turns out SQLite have db level locking so I get very frequest db locking error when stress testing. Because of that, I switched to PostgreSQL to satisfy the requirements. The test on test_concurrency also make sure the concurrency write is working as expected and there's no duplicate write. Especially, on test_30_ips_concurrent_writes will access the db with atleast 30 concurrent writes.

## 3. 3 ideas for future accuracy improvements
### 1. microservices
The first idea for improvement is by making microservices. Especially, separating the EntailmentService layer to its own service. This will make the API gateway layer and the model prediction layer seperate, so we can scale the model and/or the API gateway layer as needed. By seperating the model layer we can also deploy the model seperately, so will be cleaner to deploy and manage much larger model.

### 2. better rate limiting logic
Right now the rate limiting logic is fixed window with burst-request weakness I explained. We can improve this by using the sliding window logic. Also, right now the rate limit is saved on PostgreSQL DB. I think, for specifically rate limit, it's better to save it on memory DB such as Redis because it's not important perpetual data.

### 3. improve the model
Right now we only use the pretrained weights and use the small version of the model. We can improve accuracy by using larger version of the model, or finding better model. Other than that, we can also fine tune the model to predict it as domain specific that we want, so we can have better accuracy performance.

# Automated tests (pytest)
the automated tests are in the tests folder for each package, which can be run using `uv run poe test` 
 
# API documentation (OpenAPI YAML or Markdown tables, etc.)
the API documentation is in `openapi.yaml`, which are generated using `spectacular` package.

# Other documentations
Becauyse I use Sentence-Transformers, although it's technically not "large" language model (though it's large at the time), it's still pretty considerable amount of about 500 MB for downloading the model. The caching is already handled by the Sentence-Transformers package which will cache the model to RAM after successfully downloaded.

Also, because I use pretrained model, I don't quite understand the `stats accuracy calculation` requirement in the pytest , because we just use the pretrained model as is and there's not training. So in my opinion there's no need to test the accuracy for the model.