# DjangoSubclassField
A custom Django field for use with Django-polymorphic.  Takes a PolymorphicModel and the name of the app it is in as inputs.  Can store a subclass of the given PolymorphicModel.  Written for Django 1.8 and Python 3

Example:
```python
#If your models are defined like this in an app named "pizza":
class OneToppingPizza(PolymorphicModel):
    topping_type = SubclassField(app='pizza', superclass=Topping)


class Topping(PolymorphicModel):
  ...
  
  
class Pepperoni(Topping):
  ...
  
  
class Sausage(Topping):
  ...
  
#You can call:
p = OneToppingPizza.objects.create(topping_type=Sausage)
p.topping_type #Will return the class Sausage so...
s = Sausage.objects.create()
p.topping_type == type(s) #Returns True
#PLEASE NOTE
p.topping_type = Pepperoni
p.save()
p.topping_type #This will return 'Pepperoni', the class name as text
p.refresh_from_db() #But when we refresh from the database...
p.topping_type #This will return Pepperoni, the class object
#This weird behavior is due to django not refreshing the object from the database when it is saved
```
This field is defined with a custom widget that will display all subclases of the given superclass in a ChoiceField.

