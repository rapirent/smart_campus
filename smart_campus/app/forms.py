from django import forms
from django.conf import settings

from .models import (
    Station,
    StationCategory,
    Reward,
    User,
    Beacon,
    TravelPlan,
    Question
)


class StationForm(forms.ModelForm):
    beacon = forms.CharField()
    lat = forms.FloatField()
    lng = forms.FloatField()
    main_img_num = forms.IntegerField(required=False)

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


class PartialRewardForm(forms.ModelForm):
    class Meta:
        model = Reward
        exclude = ['related_station']


class RewardForm(forms.ModelForm):
    class Meta:
        model = Reward
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(RewardForm, self).__init__(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['related_station'].required = False


class ManagerForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'group', 'role')


class BeaconForm(forms.ModelForm):
    lat = forms.FloatField()
    lng = forms.FloatField()

    class Meta:
        model = Beacon
        fields = ('beacon_id', 'name', 'description', 'owner_group')

    def __init__(self, *args, **kwargs):
        super(BeaconForm, self).__init__(*args, **kwargs)
        self.fields['owner_group'].required = False


<<<<<<< HEAD
class PartialTravelPlanForm(forms.ModelForm):
    class Meta:
        model = TravelPlan
        exclude = ['stations']
=======
class QuestionForm(forms.ModelForm):
    choice1 = forms.CharField()
    choice2 = forms.CharField()
    choice3 = forms.CharField()
    choice4 = forms.CharField()
    answer = forms.CharField()

    class Meta:
        model = Question
        fields = ('content', 'linked_station')

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields['linked_station'].required = False
>>>>>>> 3bcf46ecdab40ff13163d233968c370d77404120
