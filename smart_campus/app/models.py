from django.contrib.gis.db import models
from django.contrib.auth.base_user import (
    BaseUserManager, AbstractBaseUser
)
from django.core.files.storage import FileSystemStorage
from django.conf import settings


class Beacon(models.Model):
    beacon_id = models.CharField(max_length=200, primary_key=True)
    name = models.CharField(max_length=200, unique=True)
    description = models.CharField(max_length=200, blank=True)
    location = models.PointField(srid=4326)
    owner_group = models.ForeignKey('UserGroup', null=True, on_delete=models.SET_NULL)
    station = models.ManyToManyField('Station')

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, nickname=""):
        """
        Create and save a User instance with the given email and password
        """
        if not email:
            raise ValueError('Email address is needed.')

        user = self.model(
            email=self.normalize_email(email),
            nickname=nickname,
            role=Role.objects.get(name='User'),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    email = models.EmailField(max_length=255, unique=True, primary_key=True)
    password = models.CharField(max_length=128)
    nickname = models.CharField(max_length=254, blank=True)
    role = models.ForeignKey('Role', null=True, on_delete=models.SET_NULL)
    group = models.ForeignKey(
        'UserGroup',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    experience_point = models.IntegerField(default=0)
    earned_coins = models.IntegerField(default=0)

    answered_questions = models.ManyToManyField('Question')
    visited_beacons = models.ManyToManyField('Beacon')
    favorite_stations = models.ManyToManyField('Station')

    received_rewards = models.ManyToManyField(
        'Reward',
        through='UserReward',
    )

    # custom model manager for model 'User'
    objects = UserManager()

    USERNAME_FIELD = 'email'

    def can(self, permissions):
        return (self.role is not None and
                (self.role.permissions & permissions) == permissions)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def __str__(self):
        return '{email} ({name})'.format(
            email=self.email,
            name=self.nickname
        )


class AnonymousUser:
    def __str__(self):
        return 'AnonymousUser'

    def save(self):
        raise NotImplementedError("Django doesn't provide a DB representation for AnonymousUser.")

    def delete(self):
        raise NotImplementedError("Django doesn't provide a DB representation for AnonymousUser.")

    def set_password(self, raw_password):
        raise NotImplementedError("Django doesn't provide a DB representation for AnonymousUser.")

    def check_password(self, raw_password):
        raise NotImplementedError("Django doesn't provide a DB representation for AnonymousUser.")

    def can(self, permissions):
        return False

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    @property
    def is_anonymous(self):
        return True

    @property
    def is_authenticated(self):
        return False

    @property
    def is_active(self):
        return False

    def get_username(self):
        return ""


class UserGroup(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Reward(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(
        null=True,
        upload_to='images/reward/'
    )
    description = models.TextField(blank=True)
    related_station = models.ForeignKey(
        'Station',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name


class UserReward(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    reward = models.ForeignKey('Reward', on_delete=models.CASCADE)
    # Automatically record the time this entry created
    timestamp = models.DateTimeField(auto_now_add=True)


class Permission:
    VIEW = 0x01
    EDIT = 0x02
    ADMIN = 0xff


class Role(models.Model):
    name = models.TextField(unique=True)
    permissions = models.IntegerField()

    @staticmethod
    def insert_roles():
        """
        add/modify roles below, run with 'python manage.py shell'
        """
        roles = {
            'User': Permission.VIEW,
            'Moderator': Permission.VIEW | Permission.EDIT,
            'Administrator': Permission.ADMIN
        }
        for r in roles:
            role = Role.objects.filter(name=r).first()
            if role is None:
                role = Role(name=str(r))
            role.permissions = roles[r]
            role.save()

    def __str__(self):
        return self.name


class QuestionType:
    BINARY = 0x01
    MULTIPLE_CHOICE = 0x02


class Question(models.Model):
    content = models.CharField(max_length=254)

    question_type = models.IntegerField(
        choices=(
            (QuestionType.BINARY, 'True or False'),
            (QuestionType.MULTIPLE_CHOICE, 'MuitipleChoice'),
        ),
        default=QuestionType.MULTIPLE_CHOICE,
    )
    choices = models.ManyToManyField(
        'Choice',
        through='QuestionChoice',
    )
    linked_station = models.ForeignKey('Station', null=True, on_delete=models.SET_NULL)

    def __repr__(self):
        return str(self.id)


class Choice(models.Model):
    content = models.CharField(max_length=50)

    def __str__(self):
        return self.content


class QuestionChoice(models.Model):
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    choice = models.ForeignKey('Choice', on_delete=models.CASCADE)
    is_answer = models.BooleanField(default=False)


class Station(models.Model):
    name = models.CharField(max_length=254, unique=True)
    content = models.TextField(blank=True)
    category = models.ForeignKey('StationCategory', null=True, on_delete=models.SET_NULL)
    location = models.PointField(srid=4326, null=True, blank=True)
    owner_group = models.ForeignKey('UserGroup', null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return '{name} ({category})'.format(
            name=self.name,
            category=str(self.category)
        )

    def get_primary_image(self):
        """Get the primary image

        Returns:
            str: Image URL if the primary station image exists, None otherwise.

        """
        primary_image = StationImage.objects.filter(
            station=self,
            is_primary=True
        ).first()

        if primary_image:
            return primary_image.image.url
        return None

    def get_other_images(self):
        """Get the image excluding primary one

        Returns:
            dict: Other Images URLs

        """
        others_image = StationImage.objects.filter(
            station=self,
            is_primary=False
        ).order_by('id')

        images_url = [
            image.image.url
            for image in others_image
        ]

        return images_url


class StationCategory(models.Model):
    name = models.CharField(max_length=254, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class StationImage(models.Model):
    station = models.ForeignKey('Station', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/station/')
    is_primary = models.BooleanField(default=False)

    def __repr__(self):
        return 'Image {img_id}'.format(img_id=self.id)


class TravelPlan(models.Model):
    name = models.CharField(max_length=254)
    description = models.TextField(blank=True)
    stations = models.ManyToManyField(
        'Station',
        through='TravelPlanStations'
    )
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to="images/travel_plan/"
    )

    def __str__(self):
        return self.name


class TravelPlanStations(models.Model):
    travelplan = models.ForeignKey('TravelPlan', on_delete=models.CASCADE)
    station = models.ForeignKey('Station', on_delete=models.CASCADE)
    order = models.IntegerField()
