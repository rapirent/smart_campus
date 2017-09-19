from django.forms import (
    ModelForm,
    CharField,
    FloatField,
    ImageField,
    IntegerField
)

from django.conf import settings

from .models import(
    Station,
    StationCategory,
    Reward,
    User,
    Beacon,
    TravelPlan,
    Question
)


class StationForm(ModelForm):
    beacon = CharField()
    lat = FloatField()
    lng = FloatField()
    main_img_num = IntegerField(required=False)

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


class RewardForm(ModelForm):
    class Meta:
        model = Reward
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(RewardForm, self).__init__(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['related_station'].required = False


class ManagerForm(ModelForm):
    class Meta:
        model = User
        fields = ('email', 'group', 'role')


class BeaconForm(ModelForm):
    lat = FloatField()
    lng = FloatField()

    class Meta:
        model = Beacon
        fields = ('beacon_id', 'name', 'description', 'owner_group')

    def __init__(self, *args, **kwargs):
        super(BeaconForm, self).__init__(*args, **kwargs)
        self.fields['owner_group'].required = False


class PartialTravelPlanForm(ModelForm):
    image = ImageField(required=False)

    class Meta:
        model = TravelPlan
        exclude = ['stations']


class QuestionForm(ModelForm):
    choice1 = CharField()
    choice2 = CharField()
    choice3 = CharField()
    choice4 = CharField()
    answer = CharField()

    class Meta:
        model = Question
        fields = ('content', 'linked_station')

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields['linked_station'].required = False

