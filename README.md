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
For this assignment, we need to check if sentence1 and sentence2 have entailment or not. This is a classic NLP task, named Natural Language Inference (NLI). NLI is a task that required 2 arguments: premise and hypothesis, then it will classify if premise and hypothesis are classified as entailment, contradiction, or neutral. Or, NLI is a classification problem. Because it's a classic classification problem that takes input and prints an output, we have many ways to solve it.

One of the most common way to solve classification problem is by using machine learning models. Because language library models are allowed, for this assignment I use a Sentence-Transformers library. I specifically use the CrossEncoder model because it's the model that are used for classification task. I use pretrained models that are trained to solve NLI task (https://sbert.net/docs/cross_encoder/pretrained_models.html#nli). For this task I use model this model: `MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli` (https://huggingface.co/MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli). The reason I choose this is because in the assignment description it has Japanese input, so I need a model that can handle multilanguage input. Also because it's just a mini-project, we don't need a large model and only need the smallest size model.

When we use the model using .predict() function, it will output 3 values, which are in order are values of: [entailment, neutral, contradiction]. These are specified in the model description. The values are also on logits, so we must convert it to 0-100 using softmax function, so we get nice looking score/prediction value. Also, because on this task we only need 2 label: entailment and not entailment, I combine the score of neutral and contradiction to create not entailment label. With this configuration, we can create the judgement API to work as the specification.

Besides the core /judge API, there's also one more task for this assignment: rate limit. For rate limit algorithm, I use the fixed window algorithm. This algorithm will store the 1st time the request are coming, and then will increase the counter until it reach max limit of the rate, which then will return the RateLimitExceeded error. When a request exceed the 1st time along the specified time window, it will then reset the counter so the request can be allowed again.

The reason why I choose the fixed window algorithm is because it's very easy to implement, and because the idempotency key is just client_ip, we only need to create 


