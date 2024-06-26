"""Test ChatMistral chat model."""

import json
from typing import Any

from langchain_core.messages import AIMessageChunk
from langchain_core.pydantic_v1 import BaseModel

from langchain_mistralai.chat_models import ChatMistralAI


def test_stream() -> None:
    """Test streaming tokens from ChatMistralAI."""
    llm = ChatMistralAI()

    for token in llm.stream("I'm Pickle Rick"):
        assert isinstance(token.content, str)


async def test_astream() -> None:
    """Test streaming tokens from ChatMistralAI."""
    llm = ChatMistralAI()

    async for token in llm.astream("I'm Pickle Rick"):
        assert isinstance(token.content, str)


async def test_abatch() -> None:
    """Test streaming tokens from ChatMistralAI"""
    llm = ChatMistralAI()

    result = await llm.abatch(["I'm Pickle Rick", "I'm not Pickle Rick"])
    for token in result:
        assert isinstance(token.content, str)


async def test_abatch_tags() -> None:
    """Test batch tokens from ChatMistralAI"""
    llm = ChatMistralAI()

    result = await llm.abatch(
        ["I'm Pickle Rick", "I'm not Pickle Rick"], config={"tags": ["foo"]}
    )
    for token in result:
        assert isinstance(token.content, str)


def test_batch() -> None:
    """Test batch tokens from ChatMistralAI"""
    llm = ChatMistralAI()

    result = llm.batch(["I'm Pickle Rick", "I'm not Pickle Rick"])
    for token in result:
        assert isinstance(token.content, str)


async def test_ainvoke() -> None:
    """Test invoke tokens from ChatMistralAI"""
    llm = ChatMistralAI()

    result = await llm.ainvoke("I'm Pickle Rick", config={"tags": ["foo"]})
    assert isinstance(result.content, str)


def test_invoke() -> None:
    """Test invoke tokens from ChatMistralAI"""
    llm = ChatMistralAI()

    result = llm.invoke("I'm Pickle Rick", config=dict(tags=["foo"]))
    assert isinstance(result.content, str)


def test_structured_output() -> None:
    llm = ChatMistralAI(model="mistral-large-latest", temperature=0)
    schema = {
        "title": "AnswerWithJustification",
        "description": (
            "An answer to the user question along with justification for the answer."
        ),
        "type": "object",
        "properties": {
            "answer": {"title": "Answer", "type": "string"},
            "justification": {"title": "Justification", "type": "string"},
        },
        "required": ["answer", "justification"],
    }
    structured_llm = llm.with_structured_output(schema)
    result = structured_llm.invoke(
        "What weighs more a pound of bricks or a pound of feathers"
    )
    assert isinstance(result, dict)


def test_streaming_structured_output() -> None:
    llm = ChatMistralAI(model="mistral-large", temperature=0)

    class Person(BaseModel):
        name: str
        age: int

    structured_llm = llm.with_structured_output(Person)
    strm = structured_llm.stream("Erick, 27 years old")
    chunk_num = 0
    for chunk in strm:
        assert chunk_num == 0, "should only have one chunk with model"
        assert isinstance(chunk, Person)
        assert chunk.name == "Erick"
        assert chunk.age == 27
        chunk_num += 1


def test_streaming_tool_call() -> None:
    llm = ChatMistralAI(model="mistral-large", temperature=0)

    class Person(BaseModel):
        name: str
        age: int

    tool_llm = llm.bind_tools([Person])

    # where it calls the tool
    strm = tool_llm.stream("Erick, 27 years old")

    additional_kwargs = None
    for chunk in strm:
        assert isinstance(chunk, AIMessageChunk)
        assert chunk.content == ""
        additional_kwargs = chunk.additional_kwargs

    assert additional_kwargs is not None
    assert "tool_calls" in additional_kwargs
    assert len(additional_kwargs["tool_calls"]) == 1
    assert additional_kwargs["tool_calls"][0]["function"]["name"] == "Person"
    assert json.loads(additional_kwargs["tool_calls"][0]["function"]["arguments"]) == {
        "name": "Erick",
        "age": 27,
    }

    # where it doesn't call the tool
    strm = tool_llm.stream("What is 2+2?")
    acc: Any = None
    for chunk in strm:
        assert isinstance(chunk, AIMessageChunk)
        acc = chunk if acc is None else acc + chunk
    assert acc.content != ""
    assert "tool_calls" not in acc.additional_kwargs
