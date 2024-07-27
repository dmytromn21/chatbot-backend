import datetime
import json

from openai.types.chat import (
    ChatCompletion,
    ChatCompletionToolParam,
)


def build_search_function() -> list[ChatCompletionToolParam]:
    return [
        {
            "type": "function",
            "function": {
                "name": "search_database",
                "description": "Search PostgreSQL database for relevant events based on user query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_query": {
                            "type": "string",
                            "description": "Query string to use for full text search, e.g. 'live concert'",
                        },
                        "price_filter": {
                            "type": "object",
                            "description": "Filter search results based on price of the events",
                            "properties": {
                                "comparison_operator": {
                                    "type": "string",
                                    "description": "Operator to compare the column value, either '>', '<', '>=', '<=', '='",  # noqa
                                },
                                "value": {
                                    "type": "number",
                                    "description": "Value to compare against, e.g. 30",
                                },
                            },
                        },
                        "category_filter": {
                            "type": "object",
                            "description": "Filter search results based on category of the event",
                            "properties": {
                                "comparison_operator": {
                                    "type": "string",
                                    "description": "Operator to compare the column value, either '=' or '!='",
                                },
                                "value": {
                                    "type": "string",
                                    "description": "Value to compare against, e.g. Concert",
                                },
                            },
                        },
                        "date_filter": {
                            "type": "object",
                            "description": "Filter search results based on the start date of the events. Handles both specific dates and relative date references.",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["specific", "relative"],
                                    "description": "Indicates whether the date is a specific date or a relative reference.",
                                },
                                "specific_date": {
                                    "type": "object",
                                    "properties": {
                                        "comparison_operator": {
                                            "type": "string",
                                            "enum": [">", "<", ">=", "<=", "="],
                                            "description": "Operator to compare the column value",
                                        },
                                        "value": {
                                            "type": "string",
                                            "description": "Specific date in YYYY-MM-DD format, e.g., 2024-07-25",
                                        },
                                    },
                                    "required": ["comparison_operator", "value"],
                                },
                                "relative_date": {
                                    "type": "object",
                                    "properties": {
                                        "reference": {
                                            "type": "string",
                                            "description": "Relative date reference, e.g., 'today', 'tomorrow', 'next week', 'next month'",
                                        },
                                        "range": {
                                            "type": "string",
                                            "enum": ["exact", "before", "after", "between"],
                                            "description": "Specifies how to interpret the relative date reference",
                                        },
                                        "duration": {
                                            "type": "object",
                                            "properties": {
                                                "value": {
                                                    "type": "integer",
                                                    "description": "Numeric value for duration",
                                                },
                                                "unit": {
                                                    "type": "string",
                                                    "enum": ["day", "week", "month"],
                                                    "description": "Unit of duration",
                                                },
                                            },
                                            "required": ["value", "unit"],
                                        },
                                    },
                                    "required": ["reference", "range"],
                                },
                            },
                            "required": ["type"],
                        },
                    },
                    "required": ["search_query"],
                },
            },
        }
    ]


def extract_search_arguments(original_user_query: str, chat_completion: ChatCompletion):
    response_message = chat_completion.choices[0].message
    search_query = None
    filters = []
    if response_message.tool_calls:
        for tool in response_message.tool_calls:
            if tool.type != "function":
                continue
            function = tool.function
            if function.name == "search_database":
                arg = json.loads(function.arguments)
                # Even though its required, search_query is not always specified
                search_query = arg.get("search_query", original_user_query)
                if "price_filter" in arg and arg["price_filter"]:
                    price_filter = arg["price_filter"]
                    filters.append(
                        {
                            "column": "price",
                            "comparison_operator": price_filter["comparison_operator"],
                            "value": price_filter["value"],
                        }
                    )
                # if "category_filter" in arg and arg["category_filter"]:
                #    category_filter = arg["category_filter"]
                #    filters.append(
                #        {
                #            "column": "category",
                #            "comparison_operator": category_filter["comparison_operator"],
                #            "value": category_filter["value"],
                #        }
                #    )
                if "date_filter" in arg and arg["date_filter"]:
                    filters.append(parse_date_filter(arg["date_filter"]))

    elif query_text := response_message.content:
        search_query = query_text.strip()
    return search_query, filters


def parse_date_filter(date_filter):
    if date_filter["type"] == "specific":
        return {
            "column": "start_date_typed",
            "comparison_operator": date_filter["specific_date"]["comparison_operator"],
            "value": date_filter["specific_date"]["value"],
        }
    elif date_filter["type"] == "relative":
        relative_date = date_filter["relative_date"]
        today = datetime.date.today()

        if relative_date["reference"] == "today":
            date_value = today
        elif relative_date["reference"] == "tomorrow":
            date_value = today + datetime.timedelta(days=1)
        elif relative_date["reference"] == "next week":
            date_value = today + datetime.timedelta(weeks=1)
        elif relative_date["reference"] == "next month":
            date_value = today + datetime.timedelta(days=30)  # Approximate
        else:
            raise ValueError(f"Unsupported relative date reference: {relative_date['reference']}")

        if "duration" in relative_date:
            duration_value = relative_date["duration"]["value"]
            duration_unit = relative_date["duration"]["unit"]
            if duration_unit == "day":
                end_date = date_value + datetime.timedelta(days=duration_value)
            elif duration_unit == "week":
                end_date = date_value + datetime.timedelta(weeks=duration_value)
            elif duration_unit == "month":
                end_date = date_value + datetime.timedelta(days=30 * duration_value)  # Approximate

        if relative_date["range"] == "exact":
            return {
                "column": "start_date_typed",
                "comparison_operator": "=",
                "value": date_value.isoformat(),
            }
        elif relative_date["range"] == "before":
            return {
                "column": "start_date_typed",
                "comparison_operator": "<",
                "value": date_value.isoformat(),
            }
        elif relative_date["range"] == "after":
            return {
                "column": "start_date_typed",
                "comparison_operator": ">",
                "value": date_value.isoformat(),
            }   
        elif relative_date["range"] == "between":
            if "duration" not in relative_date:
                raise ValueError("Duration is required for 'between' range")
            return {
                "column": "start_date_typed",
                "comparison_operator": "BETWEEN",
                "value": (date_value.isoformat(), end_date.isoformat()),
            }
        else:
            raise ValueError(f"Unsupported date range: {relative_date['range']}")
