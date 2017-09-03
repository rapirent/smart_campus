from django import forms

from .models import Station


class StationForm(forms.ModelForm):
    beacon = forms.CharField()
    lat = forms.FloatField()
    lng = forms.FloatField()
    img1 = forms.ImageField(required=False)
    img2 = forms.ImageField(required=False)
    img3 = forms.ImageField(required=False)
    img4 = forms.ImageField(required=False)
    main_img_num = forms.IntegerField()

    class Meta:
        model = Station
        fields = ('name', 'content', 'category')
