# Generated migration for SLAConfig model

import uuid
from django.db import migrations, models


def create_default_sla_configs(apps, schema_editor):
    """Create default SLA configurations for all priority levels"""
    SLAConfig = apps.get_model('tickets', 'SLAConfig')
    
    default_configs = [
        {
            'priority': 'urgent',
            'response_time': 1,  # 1 hour
            'resolution_time': 4,  # 4 hours
            'description': 'Urgent priority - Critical issues requiring immediate attention',
            'is_active': True,
        },
        {
            'priority': 'high',
            'response_time': 4,  # 4 hours
            'resolution_time': 8,  # 8 hours
            'description': 'High priority - Important issues that need quick resolution',
            'is_active': True,
        },
        {
            'priority': 'medium',
            'response_time': 8,  # 8 hours
            'resolution_time': 24,  # 24 hours
            'description': 'Medium priority - Standard issues with normal handling time',
            'is_active': True,
        },
        {
            'priority': 'low',
            'response_time': 24,  # 24 hours
            'resolution_time': 72,  # 72 hours
            'description': 'Low priority - Non-urgent issues that can be handled when time permits',
            'is_active': True,
        },
    ]
    
    for config in default_configs:
        SLAConfig.objects.create(**config)


def reverse_default_sla_configs(apps, schema_editor):
    """Remove default SLA configurations"""
    SLAConfig = apps.get_model('tickets', 'SLAConfig')
    SLAConfig.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0005_ticketattachment'),
    ]

    operations = [
        migrations.CreateModel(
            name='SLAConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('priority', models.CharField(choices=[('low', 'low'), ('medium', 'medium'), ('high', 'high'), ('urgent', 'urgent')], max_length=10, unique=True)),
                ('response_time', models.IntegerField(help_text='Response time in hours')),
                ('resolution_time', models.IntegerField(help_text='Resolution time in hours')),
                ('description', models.TextField(blank=True, default='')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'SLA Configuration',
                'verbose_name_plural': 'SLA Configurations',
                'ordering': ['priority'],
            },
        ),
        # Add default SLA configurations
        migrations.RunPython(create_default_sla_configs, reverse_default_sla_configs),
    ]
