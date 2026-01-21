# Generated migration for default ticket categories

from django.db import migrations


def create_default_categories(apps, schema_editor):
    """Create default ticket categories"""
    TicketCategory = apps.get_model('tickets', 'TicketCategory')
    
    default_categories = [
        {'name': 'Network', 'description': 'Network connectivity issues'},
        {'name': 'Hardware', 'description': 'Hardware problems and equipment issues'},
        {'name': 'Software', 'description': 'Software installation and configuration'},
        {'name': 'Account', 'description': 'User account and access issues'},
        {'name': 'Email', 'description': 'Email and communication problems'},
        {'name': 'Security', 'description': 'Security concerns and incidents'},
        {'name': 'Printing', 'description': 'Printer and printing issues'},
        {'name': 'Other', 'description': 'Other IT related issues'},
    ]
    
    for category in default_categories:
        TicketCategory.objects.get_or_create(
            name=category['name'],
            defaults={'description': category['description']}
        )


def reverse_default_categories(apps, schema_editor):
    """Remove default ticket categories"""
    TicketCategory = apps.get_model('tickets', 'TicketCategory')
    default_names = ['Network', 'Hardware', 'Software', 'Account', 'Email', 'Security', 'Printing', 'Other']
    TicketCategory.objects.filter(name__in=default_names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0006_slaconfig'),
    ]

    operations = [
        migrations.RunPython(create_default_categories, reverse_default_categories),
    ]
