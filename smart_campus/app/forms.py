from django.forms import (
    ModelForm,
    CharField,
    FloatField,
    ImageField,
    IntegerField
)

from django.conf import settings

from .models import Station, StationCategory, Reward


class StationForm(ModelForm):
    beacon = CharField()
    lat = FloatField()
    lng = FloatField()
    main_img_num = IntegerField()

    def __init__(self, *args, **kwargs):
        super(StationForm, self).__init__(*args, **kwargs)
        for i in range(1, settings.MAX_IMGS_UPLOAD + 1):
            field_name = 'img{0}'.format(i)
            self.fields[field_name] = ImageField(required=False)

    class Meta:
        model = Station
        fields = ('name', 'content', 'category')


class StationCategoryForm(ModelForm):
    class Meta:
        model = StationCategory
        fields = '__all__'


class PartialRewardForm(ModelForm):
    class Meta:
        model = Reward
        exclude = ['related_station']
