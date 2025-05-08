from typing import Optional, Type, TypeVar, Dict, Callable, Union, Tuple

from gamms.typing import IContext
from gamms.typing.opcodes import OpCodes

from typing import get_origin

_T = TypeVar('_T')

def check_validity(
    data_type: Type[_T],
) -> None:
    if data_type is None:
        raise TypeError('Data type cannot be None. Use Optional instead')
    elif data_type is type(None):
        return
    elif data_type is Ellipsis:
        return
    elif data_type in (int, float, str, bool):
        return
    elif not hasattr(data_type, '__module__'):
        raise TypeError(f'Data type {data_type} must be an immutable python type hint')
    elif data_type.__module__ != 'typing':
        raise TypeError(f'Data type {data_type} must be an immutable python type hint')
    elif get_origin(data_type) == Optional:
        if not hasattr(data_type, '__args__'):
            raise TypeError('Optional must have a type hint')
        for arg in data_type.__args__:
            check_validity(arg)
    elif get_origin(data_type) == Union:
        if not hasattr(data_type, '__args__'):
            raise TypeError('Union must have a type hint')
        for arg in data_type.__args__:
            check_validity(arg)
    elif get_origin(data_type) == Tuple:
        if not hasattr(data_type, '__args__'):
            raise TypeError('Tuple must have a type hint')
        for arg in data_type.__args__:
            check_validity(arg)
    else:
        raise TypeError(f'Data type {data_type} must be an immutable python type hint')


def component(
    ctx: IContext,
    struct: Optional[Dict[str, _T]] = None,
) -> Callable[[Type[_T]], Type[_T]]:
    def decorator(cls_type: Type[_T]) -> Type[_T]:
        if struct is None:
            print('No data is being tracked')
            return cls_type
        
        # Check struct is a dictionary
        if not isinstance(struct, dict):
            raise TypeError('struct must be a dictionary')
        
        # Check struct has immutable types as values
        for key, value in struct.items():
            if not isinstance(key, str):
                raise TypeError('Keys in struct must be strings')
            if key == 'name':
                raise TypeError('name is a reserved keyword for components')
            check_validity(value)
            # Make all values optional as default is None
            struct[key] = Optional[value]
            
        method_set = set(dir(cls_type))
        # Container for the recorded data
        if '__recorded_component_' in method_set:
            raise TypeError('Component already has a __recorded_component_ attribute')
        
        # Check keys in struct are not already in the class
        for key in struct:
            if key in method_set:
                raise TypeError(f'Key {key} in struct is already in the class')
        
        # Class key for the component
        cls_key = (cls_type.__module__, cls_type.__qualname__)

        # Check if the class has an arguments in the init method
        if hasattr(cls_type.__init__, '__code__'):
            # Get varnames for the init method
            varnames = cls_type.__init__.__code__.co_varnames[1:]
            if 'name' in varnames:
                raise TypeError('name is a reserved keyword for components')
            
            copy_init = cls_type.__init__
            # Create a init function with same signature but with name as first argument
            # after self and call the original init method with rest of the arguments
            def init(self, name: str, *args, **kwargs):
                if ctx.record.record():
                    ctx.record.write(
                        opCode = OpCodes.COMPONENT_CREATE,
                        data = {"name": name, "type": cls_key}
                    )
                ctx.record.add_component(name, self)
                self.__recorded_component_ = {k: None for k in struct}
                self.__recorded_component_['name'] = name
                copy_init(self, *args, **kwargs)
            
            # Set the new init method to the class
            setattr(cls_type, '__init__', init)
        else:
            # Create a init function with name as first argument
            def init(self, name: str):
                if ctx.record.record():
                    ctx.record.write(
                        opcode = OpCodes.COMPONENT_CREATE,
                        data = {"name": name, "type": cls_key}
                    )
                ctx.record.add_component(name, self)
                self.__recorded_component_ = {k: None for k in struct}
                self.__recorded_component_['name'] = name
            
            # Set the new init method to the class
            setattr(cls_type, '__init__', init)
        
        # Create a gettr method for the name attribute
        setattr(cls_type, 'name', property(lambda self: self.__recorded_component_['name']))

        # Create a classproperty for each key in struct
        for key, rtype in struct.items():
            def wrapper(key=key, rtype=rtype):
                def getter(self) -> rtype:
                    return self.__recorded_component_[key]
                
                def setter(self, value: rtype) -> None:
                    if ctx.record.record():
                        ctx.record.write(
                            opCode = OpCodes.COMPONENT_UPDATE,
                            data = {"name": self.name, "key": key, "value": value}
                        )
                    self.__recorded_component_[key] = value
                
                return property(getter, setter)
            
            setattr(cls_type, key, wrapper())
        
        if not ctx.record.is_component_registered(cls_key):
            ctx.record._component_registry[cls_key] = cls_type
            if ctx.record.record():
                ctx.record.write(
                    opCode = OpCodes.COMPONENT_REGISTER,
                    data = {'key': cls_key, 'struct': {k: str(v) for k, v in struct.items()}}
                )
        
        return cls_type
    return decorator