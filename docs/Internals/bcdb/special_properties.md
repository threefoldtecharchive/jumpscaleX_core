## special properties

### _autosave

- if set when property changes a save will be called
- std false on JSXObject
- std true on JSXConfig

### _nosave

- if set on JSX obj then the object will not be saved when save() called
- when save or delete called, will ignore
- for save the trigger set_pre is still called

### _readonly

- will give error when save or delete is called
-
