
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from party.models import ContactPurposeType, ContactMethodType, ISO3166_1Country, ISO3166_2CountrySubdivision


@registry.register_document
class ContactPurposeTypeDocument(Document):
    code = fields.TextField(
        attr='CD_TYP_CNCT_PRPS',
        fields={
            'raw': fields.TextField()
        }
    )
    name = fields.TextField(
        attr='NM_TYP_CNCT_PRPS',
        fields={
            'raw': fields.TextField()
        }
    )

    class Index:
        name = 'contactpurposetype'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 1,
        }

    class Django:
        model = ContactPurposeType


@registry.register_document
class ContactMethodTypeDocument(Document):
    code = fields.TextField(
        attr='CD_TYP_CNCT_MTH',
        fields={
            'raw': fields.TextField()
        }
    )
    name = fields.TextField(
        attr='NM_TYP_CNCT_MTH',
        fields={
            'raw': fields.TextField()
        }
    )

    class Index:
        name = 'contactmethodtype'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 1,
        }

    class Django:
        model = ContactMethodType


@registry.register_document
class ISO3166_1CountryDocument(Document):
    code = fields.TextField(
        attr='CD_CY_ISO',
        fields={
            'raw': fields.TextField()
        }
    )
    name = fields.TextField(
        attr='NM_CY',
        fields={
            'raw': fields.TextField()
        }
    )

    class Index:
        name = 'iso3166_1country'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 1,
        }

    class Django:
        model = ISO3166_1Country


@registry.register_document
class ISO3166_2CountrySubdivisionDocument(Document):
    id = fields.TextField(
        attr='ID_ISO_3166_2_CY_SBDVN'
    )
    name = fields.TextField(
        attr='NM_ISO_CY_PRMRY_SBDVN',
        fields={
            'raw': fields.TextField()
        }
    )
    country = fields.ObjectField(
        attr='CD_CY_ISO',
        properties={
            "code": fields.TextField(
                attr='CD_CY_ISO',
                fields={
                    'raw': fields.TextField()
                }
            ),
            "name": fields.TextField(
                attr='NM_CY',
                fields={
                    'raw': fields.TextField()
                }
            )
        }
    )

    class Index:
        name = 'iso3166_2countrysubdivision'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 1,
        }

    class Django:
        model = ISO3166_2CountrySubdivision
        # Optional: to ensure the CountrySubdivision will be re-saved when country is updated
        related_models = [ISO3166_1Country]

    def get_instances_from_related(self, related_instance):
        """If related_models is set, define how to retrieve the Car instance(s) from the related model.
        The related_models option should be used with caution because it can lead in the index
        to the updating of a lot of items.
        """
        if isinstance(related_instance, ISO3166_1Country):
            return related_instance.iso3166_2countrysubdivision_set.all()
