import os
from typing import List
from dotenv import load_dotenv
import json
from networkx import Graph
from openai import OpenAI
import networkx as nx
from cdlib import algorithms
import instructor
import tiktoken

from data_types import Object, ObjectType, Summary
from prompts import (
    OBJECT_EXTRACTION_PROMPT,
    SUMMARY_PROMPT,
)

load_dotenv()
client = instructor.from_openai(
    OpenAI(
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
)
model = "gpt-4o"
encoding = tiktoken.encoding_for_model("gpt-4o")


def chunk_text(texts: List[str], size: int = 600, overlap: int = 100) -> List[str]:
    chunks = []
    for text in texts:
        tokens = encoding.encode(text)

        for i in range(0, len(tokens), size - overlap):
            chunk_tokens = tokens[i : i + size]
            chunk_text = encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
    return chunks


def extract_objects(chunks: List[str]) -> List[Object]:
    objects = []
    for chunk in chunks:
        response = client.chat.completions.create(
            response_model=List[Object],
            model=model,
            messages=[
                {"role": "system", "content": OBJECT_EXTRACTION_PROMPT},
                {"role": "user", "content": chunk},
            ],
        )
        objects += response

    return objects


def summarise_objects(objects: List[Object], batch_size: int = 100) -> List[Object]:
    summarised_objects = []
    for i in range(0, len(objects), batch_size):
        objects_to_summarise = objects[i : min(i + batch_size, len(objects))]
        objs = []
        for obj in objects_to_summarise:
            if obj.type == ObjectType.ENTITY:
                e = obj.object
                objs.append(f"Entity {e.name} ({e.type}): {e.description}")
            elif obj.type == ObjectType.RELATIONSHIP:
                r = obj.object
                objs.append(
                    f"Relationship from {r.from_entity.name} to {r.to_entity.name} with label {r.label} and strength {r.strength}"
                )

        objs_str = "\n".join(objs)

        response = client.chat.completions.create(
            response_model=List[Object],
            model=model,
            messages=[
                {"role": "system", "content": SUMMARY_PROMPT},
                {"role": "user", "content": objs_str},
            ],
        )
        summarised_objects += response

    return summarised_objects


def build_graph(summaries: list[Object]) -> Graph:
    G = nx.Graph()
    for object in summaries:
        if object.type == ObjectType.ENTITY:
            G.add_node(object.object.name)
        elif object.type == ObjectType.RELATIONSHIP:
            G.add_edge(
                object.object.from_entity.name,
                object.object.to_entity.name,
                desc=object.object.label,
                strength=object.object.strength,
            )

    return G


def get_communities_from_graph(graph: Graph):
    all_communities = []

    for cc in nx.connected_components(graph):
        subgraph = graph.subgraph(cc)
        if len(subgraph.nodes) > 1:
            try:
                leiden_communities = algorithms.leiden(subgraph)
                for community in leiden_communities.communities:
                    all_communities.append(community)
            except Exception as e:
                print(f"Error processing community: {e}")
        else:
            all_communities.append(list(subgraph.nodes))
    return all_communities


def summarise_communities(communities, graph):
    summaries = []
    for community in communities:
        subgraph = graph.subgraph(community)

        # Prepare community information
        nodes = list(subgraph.nodes())
        edges = list(subgraph.edges(data=True))

        # Create a description of the community
        community_desc = (
            f"This community consists of {len(nodes)} members: {', '.join(nodes)}.\n"
        )

        # Add information about relationships
        relationships = []
        for edge in edges:
            source, target, data = edge
            desc = data.get("desc", "connected")
            strength = data.get("strength", 0)
            label = data.get("label", "")
            relationships.append(
                f"{source} is {desc} to {target} (strength: {strength:.1f}, label: {label})"
            )

        community_desc += "Relationships:\n- " + "\n- ".join(relationships)

        # Generate summary using an LLM (replace this with your actual LLM call)
        response = client.chat.completions.create(
            response_model=Summary,
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Summarise the following community based on the entities and relationships.",
                },
                {"role": "user", "content": community_desc},
            ],
        )
        summary = response.summary

        summaries.append(summary)

    return summaries


def answer_user_query(community_summaries, query):
    community_answers = []
    for summary in community_summaries:
        response = client.chat.completions.create(
            response_model=str,
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": f"Answer the user query using the provided summary: {summary}",
                },
                {"role": "user", "content": query},
            ],
        )

        community_answers.append(response)

    global_answer = client.chat.completions.create(
        response_model=str,
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Combine these answers into a single concise response.",
            },
            {"role": "user", "content": f"Answers: {community_answers}"},
        ],
    )

    return global_answer


def main():
    texts = []
    dir = "input"

    # Section 2.1: Source Documents -> Text Chunks
    for file in os.listdir(dir):
        if file.endswith(".txt"):
            path = os.path.join(dir, file)
            with open(path, "r") as f:
                texts.append(f.read())

    chunks = chunk_text(texts)

    print(f"Texts chunked in {len(chunks)} chunks.")

    # Section 2.2: Text Chunks -> Element Instances
    objects = extract_objects(chunks)
    with open("objects.jsonl", "w") as f:
        for object in objects:
            json.dump(object.object.model_dump(), f)
            f.write("\n")

    print(f"{len(objects)} objects found.")

    # Section 2.3: Element Instances -> Element Summaries
    summaries = summarise_objects(objects)
    with open("summarised_objects.jsonl", "w") as f:
        for summary in summaries:
            json.dump(summary.object.model_dump(), f)
            f.write("\n")

    print(f"{len(summaries)} summarised objects found.")

    # Section 2.4: Element Summaries -> Graph Communities
    g = build_graph(summaries)
    communities = get_communities_from_graph(g)

    print(f"{len(communities)} communities found.")

    # Section 2.5: Graph Communities -> Community Summaries
    community_summaries = summarise_communities(communities=communities, graph=g)

    print(f"{len(community_summaries)} community summaries generated.")

    # Section 2.6: Community Summaries → Community Answers → Global Answer
    query = "What are the top themes in this text?"
    answer = answer_user_query(community_summaries=community_summaries, query=query)

    print(answer)


if __name__ == "__main__":
    main()
