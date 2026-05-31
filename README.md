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

One of the most common way to solve classification problem is by using machine learning models. Because language library models are allowed, for this assignment I use a Sentence-Transformers library. I specifically use the CrossEncoder model because it's the model that are used for classification task. I use pretrained models that are trained to solve NLI task (https://sbert.net/docs/cross_encoder/pretrained_models.html#nli). For this task I use model this model: `MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli` (https://huggingface.co/MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli). The reason I choose this is because in the assignment description it has Japanese input, so I need a model that can handle multilanguage input. Also because it's just a mini-project, we don't need a large model and only need the smallest size model.

When we use the model using .predict() function, it will output 3 values, which are in order are values of: [entailment, neutral, contradiction]. These are specified in the model description. The values are also on logits, so we must convert it to 0-100 using softmax function, so we get nice looking score/prediction value. Also, because on this task we only need 2 label: entailment and not entailment, I combine the score of neutral and contradiction to create not entailment label. With this configuration, we can create the judgement API to work as the specification.

### rate limit
Besides the core /judge API, there's also one more task for this assignment: rate limit. For rate limit algorithm, I use the fixed window algorithm. This algorithm will store the 1st time the request are coming, and then will increase the counter until it reach max limit of the rate, which then will return the RateLimitExceeded error. When a request exceed the 1st time along the specified time window, it will then reset the counter so the request can be allowed again.

The reason why I choose the fixed window algorithm is because it's easy to implement, and because the idempotency key is just client_ip we only need to create 1 row per IP so it's easy to track, especially when during concurrency test that are required for this assignment, and also the DB won't grow very fast as long as I control the IP to test.

But, the fixed window algorithm have weakness too. Because it automatically reset to 0 after exceeding time limit, technically the user can abuse it and have almost double the limit at border time. For example, with rate limit 5 and time window 1s, the user request 1 time at t: 00:00:00, then at 00:00:59 the user can request 4 times, then at 00:01:01 request 5 times, making the user technically sent 10 request at ~1 second. This make it the user can have spike requests to avoiding the limit. Nevertheless, at long time it will be averaged at the specified rate limit and time window (5 req/s) because of the algorithm, so as long as we can handle the spike it's not a big breaking problem, and even then the spike is at most 2x the limit.

The better algorithm for this is the sliding window. With sliding window we calculate the start of the window as the earliest time the request created, and then counter the incoming request and storing the timestamp of each request. Everytime new request is coming, we recalculate the earliest time for the start of the window. And then if there's more data than the specified rate limit at the specified time window, it will return RateLimitExceeded, and if not, then the request is inserted, to be calculated for the future start of the window. Because the rate limit window is dynamically set according to the timestamp of each data, the spike problem that i mentioned earlier is fixed and it the incoming request will be "true" limit of 5 req/s.

But, the reason i don't use the sliding window is because we need to store all of the data (IP and timestamp) for each request that are sucessfully coming. Because of this, the data on DB can grow very fast and we need to implement something or find way to delete all the "stale" data that are not used. Also because of this, it's harder to track on concurrency test if there're no duplicate write or not. And the final reason it's because it will be slower because the time complexity is O(N), for N = rate limit, while the fixed window algorithm is just O(1). Because the assignment doesn't specify if we need to implement "true" rate limit, I decided that the fixed window algorithm is fine and satisfy the requirement.

## 2. Explanation of how judgment criteria meets requirements F1-F3
### F1
### F2
### F3
### Non functional requirements

## 3. 3 ideas for future accuracy improvements
