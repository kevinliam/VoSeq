import json
import os

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save

import flickrapi


# #####################################
# Overriding method for django Haystack
def get_model_ct_tuple(model):
    return (model._meta.app_label, model._meta.model_name)


def get_model_ct(model):
    return "%s.%s" % get_model_ct_tuple(model)


def get_identifier(obj_or_string):
    """
    Haystack uses pk as default. We run in problems when our models use custom fields
    as primary key.

    This can be fixed by setting a custom HAYSTACK_IDENTIFIER_METHOD. See
    http://django-haystack.readthedocs.org/en/v2.4.0/settings.html?highlight=haystack_identifier_method#haystack-identifier-method

    :return:
    """
    if isinstance(obj_or_string, str):
        return obj_or_string

    return u"%s.%s" % (get_model_ct(obj_or_string), obj_or_string._get_pk_val())
# #####################################


class TimeStampedModel(models.Model):
    """
    Abstract base class model to provide self-updating ``created`` and
    ``modified`` fields. Taken from the 'Two scoops of django' book (v1.8).
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Genes(models.Model):
    gene_code = models.CharField(max_length=100)
    genetic_code = models.PositiveSmallIntegerField(
        null=True,
        help_text='Translation table (as number). '
                  'See <a href="http://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi">http://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi</a>',
    )
    length = models.PositiveSmallIntegerField(
        null=True,
        help_text='Number of base pairs',
    )
    description = models.CharField(max_length=255, blank=True,
                                   help_text='Long gene name.')
    reading_frame = models.PositiveSmallIntegerField(
        null=True,
        help_text='Either 1, 2 or 3',
    )
    notes = models.TextField(blank=True)
    aligned = models.CharField(
        max_length=6, choices=(
            ('yes', 'yes'),
            ('no', 'no'),
            ('notset', 'notset'),
        ),
        default='notset',
    )
    intron = models.CharField(max_length=255, blank=True)
    prot_code = models.CharField(
        max_length=6, choices=(
            ('yes', 'yes'),
            ('no', 'no'),
            ('notset', 'notset'),
        ),
        default='notset',
    )
    gene_type = models.CharField(max_length=255, blank=True, help_text='Nuclear, mitochondrial.')
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.gene_code

    class Meta:
        verbose_name_plural = 'Genes'
        app_label = 'public_interface'


class GeneSets(models.Model):
    geneset_name = models.CharField(max_length=75, blank=False)
    geneset_creator = models.CharField(max_length=75, blank=False)
    geneset_description = models.CharField(max_length=140, blank=True)
    geneset_list = models.TextField(blank=False, help_text='As items separated by linebreak.')

    def save(self, *args, **kwargs):
        tmp = [i.strip() for i in self.geneset_list.splitlines() if len(i) > 0]
        self.geneset_list = '\n'.join(tmp)
        super(GeneSets, self).save(*args, **kwargs)

    def __str__(self):
        return self.geneset_name

    class Meta:
        verbose_name_plural = 'Gene sets'
        app_label = 'public_interface'


class TaxonSets(models.Model):
    taxonset_name = models.CharField(max_length=75, blank=False)
    taxonset_creator = models.CharField(max_length=75, blank=False)
    taxonset_description = models.CharField(max_length=140, blank=True)
    taxonset_list = models.TextField(help_text='As items separated by linebreak.')

    def save(self, *args, **kwargs):
        tmp = [i.strip() for i in self.taxonset_list.splitlines() if len(i) > 0]
        self.taxonset_list = '\n'.join(tmp)
        super(TaxonSets, self).save(*args, **kwargs)

    def __str__(self):
        return self.taxonset_name

    class Meta:
        verbose_name_plural = 'Taxon sets'
        app_label = 'public_interface'


class Vouchers(TimeStampedModel):
    MALE = 'male'
    FEMALE = 'female'
    LARVA = 'larva'
    WORKER = 'worker'
    QUEEN = 'queen'
    UNKNOWN = 'unknown'
    SEX_CHOICES = (
        (MALE, 'male'),
        (FEMALE, 'female'),
        (LARVA, 'larva'),
        (WORKER, 'worker'),
        (QUEEN, 'queen'),
        (UNKNOWN, 'unknown'),
    )

    DONT_KNOW = 'unknown'
    YES = 'yes'
    NO = 'not'
    TYPE_SPECIES_CHOICES = (
        (DONT_KNOW, 'unknown'),
        (YES, 'yes'),
        (NO, 'not'),
    )

    SPREAD = 'spread'
    ENVELOPE = 'in envelope'
    PHOTO = 'only photo'
    NONE = 'no voucher'
    DESTROYED = 'destroyed'
    LOST = 'lost'
    VOUCHER_CHOICES = (
        (SPREAD, 'spread'),
        (ENVELOPE, 'in envelope'),
        (PHOTO, 'only photo'),
        (NONE, 'no voucher'),
        (DESTROYED, 'destroyed'),
        (LOST, 'lost'),
        (UNKNOWN, 'unknown'),
    )
    code = models.CharField(max_length=300, unique=True, primary_key=True, help_text="Voucher code.")
    orden = models.TextField(blank=True)
    superfamily = models.TextField(blank=True)
    family = models.TextField(blank=True)
    subfamily = models.TextField(blank=True)
    tribe = models.TextField(blank=True)
    subtribe = models.TextField(blank=True)
    genus = models.TextField(blank=True)
    species = models.TextField(blank=True)
    subspecies = models.TextField(blank=True)
    country = models.TextField(blank=True)
    specific_locality = models.TextField(help_text="Locality of origin for this specimen.", blank=True)
    type_species = models.CharField(max_length=100, choices=TYPE_SPECIES_CHOICES,
                                    help_text="Is this a type species?")
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    max_altitude = models.IntegerField(blank=True, null=True, help_text="Enter altitude in meters above sea level.")
    min_altitude = models.IntegerField(blank=True, null=True, help_text="Enter altitude in meters above sea level.")
    collector = models.TextField(blank=True)
    date_collection = models.DateField(null=True)  # TODO check if better blank null rather than null true
    extraction = models.TextField(help_text="Number of extraction event.", blank=True)
    extraction_tube = models.TextField(help_text="Tube containing DNA extract.", blank=True)
    date_extraction = models.DateField(null=True)
    extractor = models.TextField(blank=True)
    voucher_locality = models.TextField(blank=True)
    published_in = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    edits = models.TextField(blank=True, null=True)
    latest_editor = models.TextField(blank=True, null=True)
    hostorg = models.TextField(help_text="Hostplant or other host.", blank=True)
    sex = models.CharField(max_length=100, choices=SEX_CHOICES, blank=True)
    voucher = models.CharField(max_length=100, choices=VOUCHER_CHOICES, blank=True,
                               help_text="Voucher status.")
    voucher_code = models.TextField(help_text="Alternative code of voucher specimen.",
                                    blank=True)
    code_bold = models.TextField(help_text="Optional code for specimens kept in the BOLD database.",
                                 blank=True)
    determined_by = models.TextField(help_text="Person that identified the taxon for this specimen.",
                                     blank=True)
    author = models.TextField(help_text="Person that described this taxon.", blank=True)

    class Meta:
        verbose_name_plural = 'Vouchers'
        app_label = 'public_interface'

    def __str__(self):
        return self.code


class Sequences(models.Model):
    code = models.ForeignKey(Vouchers, help_text='This is your voucher code.')
    gene_code = models.CharField(max_length=100)
    sequences = models.TextField(blank=True)
    accession = models.CharField(max_length=100, blank=True)
    lab_person = models.CharField(max_length=100, blank=True)
    time_created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    time_edited = models.DateTimeField(auto_now=True, null=True, blank=True)
    notes = models.TextField(blank=True)
    genbank = models.NullBooleanField()
    total_number_bp = models.IntegerField(blank=True, null=True)
    number_ambiguous_bp = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Sequences'
        app_label = 'public_interface'

    def save(self, *args, **kwargs):
        ambiguous_seq_length = self.sequences.count('?') + self.sequences.count('-')
        ambiguous_seq_length += self.sequences.count('N') + self.sequences.count('n')
        self.number_ambiguous_bp = ambiguous_seq_length
        self.total_number_bp = len(str(self.sequences))
        super(Sequences, self).save(*args, **kwargs)

    def __str__(self):
        return self.code.code + ' ' + self.gene_code


class Primers(models.Model):
    for_sequence = models.ForeignKey(Sequences, help_text='relation to Sequences table with reference '
                                                          'for code and gene_code.')
    primer_f = models.CharField(max_length=100, blank=True)
    primer_r = models.CharField(max_length=100, blank=True)

    class Meta:
        app_label = 'public_interface'


class FlickrImages(models.Model):
    voucher = models.ForeignKey(
        Vouchers,
        help_text='Relation with id of voucher. Save as lower case.',
    )
    voucher_image = models.URLField(help_text="URLs of the Flickr page.")
    thumbnail = models.URLField(help_text="URLs for the small sized image from Flickr.")
    flickr_id = models.CharField(max_length=100, help_text="ID numbers from Flickr for our photo.")
    image_file = models.ImageField(help_text="Placeholder for image file so we can send it to Flickr. "
                                             "The file has been deleted right after upload.")

    class Meta:
        verbose_name_plural = 'Flickr Images'
        app_label = 'public_interface'

    def save(self, *args, **kwargs):
        post_save.connect(self.update_flickr_image, sender=FlickrImages, dispatch_uid="update_flickr_image_count")
        self.delete_local_photo(self.image_file)
        super(FlickrImages, self).save(*args, **kwargs)

    def delete_local_photo(self, image_filename):
        file_path = os.path.join(settings.MEDIA_ROOT, str(image_filename))
        if os.path.isfile(file_path):
            os.remove(file_path)

    def update_flickr_image(self, instance, **kwargs):
        my_api_key = settings.FLICKR_API_KEY
        my_secret = settings.FLICKR_API_SECRET
        flickr = flickrapi.FlickrAPI(my_api_key, my_secret)
        flickr.authenticate_via_browser(perms='write')

        filename = os.path.join(settings.MEDIA_ROOT, str(instance.image_file))

        if instance.flickr_id == '':
            title = self.make_title(instance)
            description = self.make_description(instance)
            tags = self.make_tags(instance)

            rsp = flickr.upload(filename, title=title, description=description,
                                tags=tags)

            instance.flickr_id = rsp.findtext('photoid')

            info = flickr.photos.getInfo(photo_id=instance.flickr_id, format="json")
            info = json.loads(info.decode('utf-8'))
            instance.voucher_image = info['photo']['urls']['url'][0]['_content']

            farm = info['photo']['farm']
            server = info['photo']['server']
            secret = info['photo']['secret']
            thumbnail_url = 'https://farm{}.staticflickr.com/{0}/{1}_{2}_m_d.jpg'.format(farm, server, instance.flickr_id, secret)
            instance.thumbnail = thumbnail_url
            instance.save()

    def make_title(self, instance):
        title = '{} {} {}'.format(
            instance.voucher.code,
            instance.voucher.genus,
            instance.voucher.species,
        )
        return title

    def make_description(self, instance):
        description = '{}. {}. {}'.format(
            instance.voucher.country,
            instance.voucher.specific_locality,
            instance.voucher.published_in,
        )
        return description

    def make_tags(self, instance):
        tags = [
            instance.voucher.country,
            instance.voucher.family,
            instance.voucher.subfamily,
            instance.voucher.tribe,
            instance.voucher.subtribe,
            instance.voucher.genus,
            instance.voucher.species,
        ]
        tags = '"' + '" "'.join(tags) + '"'
        return tags


class LocalImages(models.Model):
    """Voucher images saved in local system."""
    voucher = models.ForeignKey(
        Vouchers,
        help_text='Relation with id of voucher.',
    )
    voucher_image = models.ImageField(help_text="voucher photo.")

    class Meta:
        verbose_name_plural = 'Local Images'
        app_label = 'public_interface'
