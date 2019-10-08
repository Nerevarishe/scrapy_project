from mongoengine import Document, StringField, ListField


class DrugRecord(Document):
    drug_name = StringField()
    atc_code = StringField()
    active_substances_rus = ListField()
    owners = StringField()
    distributor = StringField()
