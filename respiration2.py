from __future__ import annotations

from functools import cached_property
from . import utils
from typing import (
  TypedDict,
  Optional,
  Generic,
  TypeVar,
  Iterable,
  Generator,
  overload
)
import json
import discord

main_path = "./Json"
_T = TypeVar('_T')

class TypedForm(TypedDict):
  name: str
  roles: list[str]
  require: int
  damege: int
  stamina: int
  title: Optional[str]
  description: Optional[str]
  url: Optional[str]
  forms: list[TypedForm]

class TypedRep(TypedDict):
  name: str
  role: Optional[str]
  title: Optional[str]
  descrition: Optional[str]
  url: Optional[str]
  forms: list[TypedForm]

class RepAlreadyExists(Exception):
  def __init__(self, ep: Rep, /) -> None:
    self.ep = ep
    super().__init__(f"{ep.__class__.__name__}: {ep.name} already exists!")
class Rep:
  @overload
  def __init__(self, data: TypedRep) -> None: ...
  @overload
  def __init__(
    self,
    name: str,
    role: Optional[discord.Role],
    title: Optional[str],
    description: Optional[str],
    url: Optional[str],
    forms: list[TypedForm]
  ) -> None: ...
  def __init__(self, data: Optional[TypedRep]=None, **_data) -> None:
    data = {**(data if not data is None else {}), **_data}
    self.name: str = data["name"]
    self.roleID: Optional[int] = (data["role"] if data['role'] is None else int(data["role"]))
    self.title: Optional[str] = data["title"]
    self.description: Optional[str] = data["description"]
    self.url: Optional[str] = data["url"]
    self._forms: list[TypedForm] = data["forms"]
  def __repr__(self) -> str:
    return f"{self.__class__.__name__}(name={self.name!r})"
  def __eq__(self, other: Rep):
    if not isinstance(other, Rep) or not issubclass(other.__class__, Rep):
      return False
    return self.name == other.name
  @cached_property
  def forms(self) -> ListedForm[Form]:
    return ListedForm(self, map(lambda data: Form(self, data), self._forms))
  @property
  def data(self) -> TypedRep:
    return {
      "name": self.name,
      "role": self.roleID,
      "title": self.title,
      "description": self.description,
      "url": self.url,
      "forms": [form.data for form in self.forms]
    }

T = TypeVar('T', bound=Rep)

class Form:
  @overload
  def __init__(self, cls: T, data: TypedForm, /) -> None: ...
  @overload
  def __init__(
    self,
    cls: T, *,
    name: str,
    roles: list[str],
    require: int,
    damege: int,
    stamina: int,
    title: Optional[str],
    description: Optional[str],
    url: Optional[str],
    forms: list[TypedForm]
  ) -> None: ...
  def __init__(self, cls: T, data: TypedForm=None, /, **kwgs) -> None:
    data = {**(data if isinstance(data, dict) else {}), **kwgs}
    self.ep = cls

    self.name: str = data["name"]
    self.rolesID: list[int] = [int(id) for id in (data["roles"] if isinstance(data["roles"], list) else [])]
    self.require: int = data["require"]
    self.damege: int = data["damege"]
    self.stamina: int = data["stamina"]
    self.title: Optional[str] = data["title"]
    self.description: Optional[str] = data["description"]
    self.url: Optional[str] = data["url"]
    self._forms: list[TypedForm] = data["forms"]
  def __repr__(self) -> str:
    return f"Form(type={self.ep} name={self.name!r})"
  def __eq__(self, other: Form) -> bool:
    if not isinstance(other, Form):
      return False
    return self.name.lower() == other.name.lower()
  @property
  def data(self) -> TypedForm:
    return {
      "name": self.name,
      "roles": list(map(str, self.rolesID)),
      "require": self.require,
      "damege": self.damege,
      "stamina": self.stamina,
      "title": self.title,
      "description": self.description,
      "url": self.url,
      "forms": self._forms
    }
class FormAlreadyExists(Exception):
  def __init__(self, form: Form) -> None:
    self.form = form
    self.ep = form.ep
    super().__init__(f"Form: {form.name!r} already exists in {form.ep.__class__.__name__}: {form.ep.name!r}!")
class ListedForm(list, Generic[_T]):
  def __init__(self, rep: T, mapped: map[Form], /) -> None:
    super().__init__(mapped)
    self.ep = rep
  def append(self, __object: Form, /) -> Form:
    if __object in [*respirations.forms, *kekkijutsus.forms]:
      raise FormAlreadyExists(next((form for form in [*respirations.forms, *kekkijutsus.forms] if form.name.lower() == __object.name.lower()), None))
    super().append(__object)
    return __object
  def new(
    self,
    name: str, *,
    roles: list[discord.Role]=None,
    require: Optional[int]=None,
    damege: int,
    stamina: int,
    title: Optional[str]=None,
    description: Optional[str]=None,
    url: Optional[str]=None
  ) -> Form: return self.append(Form(
    self.ep,
    name=name,
    roles=roles,
    require=(require if not require is None else 1),
    damege=damege,
    stamina=stamina,
    title=title,
    description=description,
    url=url,
    forms=[]
  ))
  def get(self, name: str) -> Form:
    return utils.get(self, name=name)
    
class ListedRep(list, Generic[T]):
  def __init__(self, cls: type[T], local: str) -> None:
    super().__init__(get(cls, local=local))
    self.cls = cls
    self.local = local
  @property
  def forms(self) -> list[Form]:
    forms: list[Form] = []
    for rep in self: 
      forms += rep.forms
    return forms
  def reload(self,) -> None:
    return save(self, local=self.local)
  def append(self, __object: T, /) -> T:
    if __object in [*respirations, *kekkijutsus]:
      raise RepAlreadyExists(__object)
    super().append(__object)
    save(self, local=self.local)
    return self[-1]
  def new(
    self,
    name: str, /, *,
    role: Optional[discord.Role]=None,
    title: Optional[str]=None,
    description: Optional[str]=None,
    url: Optional[str]=None
  ) -> T:
    return self.append(self.cls(
      name=name,
      role=role,
      title=title,
      description=description,
      url=url,
      forms=[]
    ))
  def get(self, name: str, /) -> Optional[T]:
    return utils.get(self, name=name)
def get(cls: type[T], /, local: str) -> map[T]:
  try:
    with open(local, 'r', encoding='utf8') as fp:
      return map(cls, json.load(fp))
  except:
    return map(cls, [])
def save(cls: Iterable[T], /, local: str) -> None:
  with open(local, 'w', encoding='utf8') as fp:
    json.dump(list(map(lambda cls: cls.data, cls)), fp)

class Respiration(Rep): ...
class Kekkijutsu(Rep): ...

respirations = ListedRep(Respiration, f"{main_path}/Respiration.json")
kekkijutsus = ListedRep(Kekkijutsu, f"{main_path}/Kekkijutsu.json")