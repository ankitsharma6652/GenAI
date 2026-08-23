from typing import TypedDict


class Person(TypedDict):

    name: str
    age: int

new_person: Person = {'name':'sachin', 'age':"32"}

print(new_person)
print(type(new_person))