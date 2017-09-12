from django import forms
from django.conf import settings

from .models import Station, StationCategory, Reward


class StationForm(forms.ModelForm):
    beacon = forms.CharField()
    lat = forms.FloatField()
    lng = forms.FloatField()
    main_img_num = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        super(StationForm, self).__init__(*args, **kwargs)
        for i in range(1, settings.MAX_IMGS_UPLOAD + 1):
            field_name = 'img{0}'.format(i)
            self.fields[field_name] = forms.ImageField(required=False)

    class Meta:
        model = Station
        fields = ('name', 'content', 'category')


class CategoryForm(forms.ModelForm):
    class Meta:
        model = StationCategory
        fields = '__all__'


class RewardForm(forms.ModelForm):
    class Meta:
        model = Reward
        fields = '__all__'