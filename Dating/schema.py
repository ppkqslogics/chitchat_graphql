import os
import graphene
import pyrebase
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import BinaryField
from graphene_django import DjangoObjectType
from Dating.models import *
from graphene_file_upload.scalars import Upload

firebaseConfig = {
    "apiKey": "AIzaSyBeglnz8M607Co1aiqR5ZxJ7Nj2Mg2BmQw",
    "authDomain": "cc-dating.firebaseapp.com",
    "databaseURL": "https://cc-dating-default-rtdb.firebaseio.com",
    "projectId": "cc-dating",
    "storageBucket": "cc-dating.appspot.com",
    "messagingSenderId": "591304592363",
    "appId": "1:591304592363:web:c6a03443fc66f4d1dee7ae",
    "measurementId": "G-SGY5E5D7L3"

}

firebaseApp = pyrebase.initialize_app(firebaseConfig)
storage = firebaseApp.storage()

def matching(list1, list2):
    res = [val for val, val in enumerate(list1) if val in set(list2)]

    if len(res) == 5:
        return 100
    elif len(res) == 4:
        return 80
    elif len(res) == 3:
        return 60
    elif len(res) == 2:
        return 40
    elif len(res) == 1:
        return 20
    else:
        return 0

class LookingForInfo(DjangoObjectType):
    class Meta:
        model = Looking_for

class UserProfileInfo(DjangoObjectType):
    class Meta:
        model = User_Profile

class ProfileMatchInfo(DjangoObjectType):
    class Meta:
        model = Profile_Match
        field = '__all__'

class UserInput(graphene.InputObjectType):
    name = graphene.String()
    dob = graphene.Date()
    gender = graphene.String()
    looking_for = graphene.String()
    bio = graphene.String()
    study_major = graphene.String()
    study_uni = graphene.String()
    work_position = graphene.String()
    company_name = graphene.String()
    height_ft = graphene.Int()
    height_in = graphene.Int()
    exercise = graphene.String()
    drinking = graphene.String()
    smoking = graphene.String()
    pets = graphene.String()
    fav_song = graphene.String()
    education_level = graphene.String()
    looking_to_meet_with = graphene.String()
    phone = graphene.String()

class InterestsInfo(DjangoObjectType):
    class Meta:
        model = Interests

class Query(object):
    looking_for_lists = graphene.List(LookingForInfo)
    interest_lists = graphene.List(InterestsInfo)

    user_list = graphene.List(UserProfileInfo)
    discover_profile = graphene.List(UserProfileInfo, user_id=graphene.String())
    user_info_detail = graphene.List(UserProfileInfo, user_id=graphene.String())
    matched_profile_list = graphene.List(ProfileMatchInfo, current_user_id=graphene.String())

    def resolve_looking_for_lists(self, info, **kwargs):
        return Looking_for.objects.using('Dating').all()

    def resolve_interest_lists(self, info, **kwargs):
        return Interests.objects.using('Dating').all()

    def resolve_user_list(self, info):
        return User_Profile.objects.using('Dating').all()

    def resolve_discover_profile(self, info, user_id):
        userProfile = User_Profile.objects.using('Dating').get(pk=user_id)
        current_user_interest_list = userProfile.interest

        _100Match = []
        _80Match = []
        _60Match = []
        _40Match = []
        _20Match = []

        allUserProfile = User_Profile.objects.using('Dating').all().exclude(id=user_id)
        print(len(allUserProfile))
        for user in allUserProfile:
            interest_list = user.interest
            matchPercent = matching(current_user_interest_list, interest_list)
            if matchPercent == 100:
                _100Match.append(user.id)
            elif matchPercent == 80:
                _80Match.append(user.id)
            elif matchPercent == 60:
                _60Match.append(user.id)
            elif matchPercent == 40:
                _40Match.append(user.id)
            elif matchPercent == 20:
                _20Match.append(user.id)

        matchList = _100Match + _80Match + _60Match + _40Match + _20Match
        print(matchList)
        if len(matchList) > 0:
            return User_Profile.objects.using('Dating').filter(pk__in=matchList)
        else:
            return User_Profile.objects.using('Dating').all().exclude(id=user_id)

    def resolve_matched_profile_list(self, info, current_user_id):
        profile = Profile_Match.objects.using('Dating').filter(pk=current_user_id)

        return profile

    def resolve_user_info_detail(self, info, user_id):
        return User_Profile.objects.using('Dating').filter(pk=user_id)

class CreateLookingfor(graphene.Mutation):
    looking_type = graphene.Field(LookingForInfo)

    class Arguments:
        looking_for_type = graphene.String()

    def mutate(self, info, looking_for_type):
        data = Looking_for(looking_for_type=looking_for_type)
        data.save(using='Dating')
        return CreateLookingfor(looking_type=data)

class DeleteLookingfor(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        id = graphene.ID()

    def mutate(self, info, id):
        data = Looking_for.objects.using('Dating').get(pk=id)
        data.delete()
        return DeleteLookingfor(ok=True)

class EditLookingfor(graphene.Mutation):
    looking_for = graphene.Field(LookingForInfo)

    class Arguments:
        looking_id = graphene.ID()
        looking_type = graphene.String()

    def mutate(self, info, looking_id, looking_type):
        data = Looking_for.objects.using('Dating').get(pk=looking_id)
        data.looking_for_type = looking_type
        data.save(using='Dating')
        return EditLookingfor(looking_for=data)

class CreateInterestType(graphene.Mutation):
    class Arguments:
        interest_name = graphene.String()
        interest_logo = Upload()

    interest_type = graphene.Field(InterestsInfo)

    def mutate(self, info, interest_name, interest_logo=None):
        if interest_logo:
            if info.context.FILES and info.context.method == 'POST':
                image = info.context.FILES['itemImage']
                cloud_url = 'Interest/' + interest_name + '.jpg'
                storage.child(cloud_url).put(image)

                interest = Interests.objects.using('Dating').create(
                interest_name=interest_name,
                interest_logo=storage.child(cloud_url).get_url(None),
                )
        interest.save(using='Dating')

        return CreateInterestType(interest_type=interest)

class DeleteInterestType(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    ok = graphene.Boolean()

    def mutate(self, info, id):
        interest = Interests.objects.using('Dating').get(pk=id)
        interest.delete()

        return DeleteInterestType(ok=True)

class CreateUserProfile(graphene.Mutation):
    class Arguments:
        userInfo = UserInput(required=False)
        profile_pic = Upload()
        interest = graphene.List(graphene.String)

    success = graphene.String()
    user_id = graphene.ID()
    error_message = graphene.String()

    def mutate(self, info, userInfo, profile_pic=None, interest=None):
        name = userInfo.name
        dob = userInfo.dob
        gender = userInfo.gender
        looking_for = userInfo.looking_for
        bio = userInfo.bio
        study_major = userInfo.study_major or None
        study_uni = userInfo.study_uni or None
        work_position = userInfo.work_position or None
        company_name = userInfo.company_name or None
        height_ft = userInfo.height_ft or None
        height_in = userInfo.height_in or None
        exercise = userInfo.exercise or None
        education_level = userInfo.education_level or None
        drinking = userInfo.drinking or None
        smoking = userInfo.smoking or None
        pets = userInfo.pets or None
        fav_song = userInfo.fav_song or None
        looking_to_meet_with = userInfo.looking_to_meet_with
        phone = userInfo.phone

        img = info.context.FILES
        img = img.getlist('profilePic')
        link = []
        if img:
            for file in img:
                t = default_storage.save(name=str(file), content=ContentFile(file.read()))
                cloud_url = 'Profile/' + str(file)
                storage.child(cloud_url).put(t)
                link.append(storage.child(cloud_url).get_url(None))
                # os.remove(t)

        else:
            link = []
        try:

            pre_account = User_Profile.objects.using('Dating').filter(phone=phone)
            for all in pre_account:
                user_id = all.id
            if pre_account is not None:
                return CreateUserProfile(success=False, user_id=user_id, error_message='Duplicate Phone Number')
        except:pass

        a = User_Profile.objects.using('Dating').create(
            name=name, dob=dob, gender=gender, looking_for=looking_for,
            bio=bio, study_major=study_major, study_uni=study_uni,
            work_position=work_position, company_name=company_name,
            height_ft=height_ft, height_in=height_in, exercise=exercise,
            education_level=education_level, drinking=drinking, smoking=smoking,
            pets=pets, fav_song=fav_song, profile_pic=link, interest=interest,
            looking_to_meet_with=looking_to_meet_with,
            phone=phone

        )
        user_id = a.id
        return CreateUserProfile(success=True, user_id=user_id)

class MatchRequestOrDecline(graphene.Mutation):
    class Arguments:
        current_user_id = graphene.ID()
        applied_user_id = graphene.String()
        match_req = graphene.Boolean()
        decline = graphene.Boolean()

    success = graphene.String()

    def mutate(self, info, current_user_id, applied_user_id, match_req=None, decline=None):
        current_user_info = User_Profile.objects.using('Dating').get(pk=current_user_id)
        if match_req is True:
            try:
                current_user_profile = Profile_Match.objects.using("Dating").get(pk=current_user_id)
                match_req_list = current_user_profile.match_req
                match_req_list = match_req_list.append(applied_user_id)
                current_user_profile.save()

            except:
                Profile_Match.objects.using('Dating').create(
                    profile_id=current_user_info,
                    matched_list=[],
                    match_req=[applied_user_id],
                    declined_list=[]
                )
            return MatchRequestOrDecline(success=True)
        elif decline is True:
            try:
                current_user_profile = Profile_Match.objects.using("Dating").get(pk=current_user_id)
                declined_list = current_user_profile.declined_list
                declined_list = declined_list.append(applied_user_id)
                current_user_profile.save()
            except:
                Profile_Match.objects.using('Dating').create(
                    profile_id=current_user_info,
                    matched_list=[],
                    match_req=[],
                    declined_list=[applied_user_id]
                )
            return MatchRequestOrDecline(success=True)

class MatchAcceptOrDecline(graphene.Mutation):
    class Arguments:
        current_user_id = graphene.ID()
        applied_user_id = graphene.String()
        match_accept = graphene.Boolean()
        decline = graphene.Boolean()

    success = graphene.String()

    def mutate(self, info, current_user_id, applied_user_id, match_accept=None, decline=None):
        current_user_profile = Profile_Match.objects.using('Dating').get(pk=current_user_id)
        if decline is True:
            decline_list = current_user_profile.declined_list
            decline_list.append(applied_user_id)
            current_user_profile.save()

        elif match_accept is True:
            accept_list = current_user_profile.matched_list
            accept_list.append(applied_user_id)
            current_user_profile.save()

        current_user_profile.match_req.remove(applied_user_id)
        current_user_profile.save()
        return MatchAcceptOrDecline(success=True)



class Mutation(graphene.ObjectType):
    create_looking_for_type = CreateLookingfor.Field()
    delete_looking_for_type = DeleteLookingfor.Field()
    edit_looking_for_type = EditLookingfor.Field()
    create_interest_type = CreateInterestType.Field()
    delete_interest_type = DeleteInterestType.Field()
    create_user_profile = CreateUserProfile.Field()
    match_req_or_decline = MatchRequestOrDecline.Field()
    match_accept_or_decline = MatchAcceptOrDecline.Field()