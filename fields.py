from __future__ import unicode_literals
from django import forms
from django.apps import apps
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.utils.deconstruct import deconstructible
from django.forms.widgets import Select
from itertools import chain


@deconstructible
class SubclassValidator(object):
    """
    Custom validator to insure the input given for a SubclassField
    is the name of a subclass of it's superclass
    """
    message = ('Ensure this value is a subclass of %(superclass)s ' +
               '(it is %(subclass)s).')
    code = 'subclass'

    def __init__(self, superclass):
        self.superclass = superclass

    def __call__(self, subclass):
        params = {'superclass': self.superclass.__name__,
                  'subclass': subclass}
        if subclass not in \
                (sub for sub in self.superclass.__subclasses__()):
            raise ValidationError(
                self.message, code=self.code, params=params)


class SubclassSelect(Select):
    """
    Selector widget subclass that uses class names to compare classes.
    """
    def render_options(self, choices, selected_choices):
        selected_choices = set(type(v).__name__ for v in selected_choices)
        output = []
        for option_value, option_label in chain(self.choices, choices):
            output.append(self.render_option(
                selected_choices, option_value, option_label))
        return '\n'.join(output)


class SubclassField(models.Field):
    """
    Custom field to allow a model to associate with a subclass
    of a PolymorphicModel.  Loosely based on TextField.  Takes
    app and superclass as strings eg. 'dispatch' for app and 'User'
    for superclass.
    """
    description = _("SubclassField")

    def __init__(self, superclass=None, app=None, *args, **kwargs):
        self.superclass = superclass
        self.app = app
        super().__init__(*args, **kwargs)
        self.validators.append(SubclassValidator(self.superclass))

    def get_internal_type(self):
        return "TextField"

    def to_python(self, value):
        if type(value) != str:
            return value
        if value is None:
            return value
        return self.string_to_class(value)

    def get_prep_lookup(self, lookup, value):
        """
        Lookups use class names.
        """
        value = super().get_prep_value(value)
        return value.__class__.__name__

    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return value
        val = self.string_to_class(value)
        return val

    def pre_save(self, model_instance, add):
        """
        The subclass name is saved as a string
        """
        initial = getattr(model_instance, self.attname)
        value = self.get_prep_value(initial)
        setattr(model_instance, self.attname, value)
        return value

    def get_prep_value(self, value):
        initial = super().get_prep_value(value)
        if initial:
            if type(initial) == str:
                return initial
            else:
                return initial.__name__
        else:
            return None

    def string_to_class(self, value):
        """
        By returning the model in this way we do not need to import
        each subclass.
        """
        app = apps.get_app_config(self.app)
        return app.models[value.lower()]

    def formfield(self, **kwargs):
        """
        Displays the custom choicefield with subclasses of
        self.superclass for the choices
        """
        subclass_names = []
        for subclass in self.superclass.__subclasses__():
            subclass_names.append((subclass.__name__, subclass.__name__))
        defaults = {
            'form_class': forms.TypedChoiceField,
            'choices': subclass_names,
            'coerce': self.string_to_class,
            'widget': SubclassSelect,
            }
        defaults.update(kwargs)
        return super().formfield(**defaults)
