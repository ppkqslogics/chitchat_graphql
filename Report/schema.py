import datetime
import graphene
from graphene_django import DjangoObjectType
from Report.models import Report, Reported_Data

class ReportInfo(DjangoObjectType):
    class Meta:
        model = Report
        fields = '__all__'

class ReportedDataInfo(DjangoObjectType):
    class Meta:
        model = Reported_Data
        fields = '__all__'

class Query(graphene.ObjectType):
    report_list = graphene.List(ReportInfo)
    report_info_by_user = graphene.List(ReportedDataInfo, user_id=graphene.String())

    def resolve_report_list(self, info, **kwargs):
        return Report.objects.all()

    def resolve_report_info_by_user(self, info, user_id):
        user_data = Reported_Data.objects.filter(user_id=user_id)
        return user_data

class CreateReportType(graphene.Mutation):
    class Arguments:
        reportType = graphene.String()

    report = graphene.Field(ReportInfo)

    def mutate(self, info, reportType):
        data = Report.objects.create(
            report_type=reportType
        )
        data.save()
        return CreateReportType(report=data)

class DeleteReport(graphene.Mutation):
    class Agruments:
        id = graphene.ID()

    ok = graphene.Boolean()

    def mutate(self, info, id):
        report = Report.objects.get(pk=id)
        report.delete()
        return DeleteReport(ok=True)

class Reported_User(graphene.Mutation):
    class Arguments:
        current_user_id = graphene.ID()
        reported_user_id = graphene.ID()
        report_type = graphene.String()
        report_text = graphene.String()

    ok = graphene.Boolean()

    def mutate(self, info, current_user_id, reported_user_id, report_type, report_text=None):

        report_info = {
            "reported_user_id": reported_user_id,
            "report": report_type,
            "reported_datetime": datetime.datetime.utcnow(),
            "report_text": report_text
        }

        try:
            current_user = Reported_Data.objects.get(pk=current_user_id)
            current_user.reported_info.append(report_info)
            current_user.save()

        except:
            current_user = Reported_Data.objects.create(
                user_id=current_user_id,
                reported_info=[report_info]
            )

        return Reported_User(ok=True)

class Mutation(graphene.ObjectType):
    create_new_report = CreateReportType.Field()
    delete_report = DeleteReport.Field()
    report_user = Reported_User.Field()
