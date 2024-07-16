# Naive GraphRAG Implementation

This is a naive implementation of the Graph RAG algorithm outlined in this [paper](https://arxiv.org/abs/2404.16130). 

The implementation follows the paper. The sections are marked in comments before every function call.

## Requirements

You will need to set your OpenAI API key in the `.env` file. 

Create a virtual environment, and install requirements: `pip install -r requirements.txt`


> [!Warning]
> Running the pipeline on a large document can be quite expensive. 

## Results

As example input I indexed the [Billionaire's build](https://www.paulgraham.com/ace.html) essay by Paul Graham and asked the question `"What are the main themes in this text?"`

Got the following response:
```
These responses indicate that various individual members (like Y Combinator, Boom, Apple, Steve Wozniak, Mark Zuckerberg, Larry Page, Sergey Brin, and YC interviews) form separate communities with no specified relationships. 

The themes, when present, often revolve around individuality and the unique existence of each member, highlighting self-reliance, singularity, and the distinct identity associated with each character.
```

which is not great, but there is some relevant insight.