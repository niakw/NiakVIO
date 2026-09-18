#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

from provider_base_store import (
    CLEAN_RECONSTRUCTION_AUTHORING_VERSION,
    CLEAN_RECONSTRUCTION_SOURCE,
    current_provider_base_template_sha256,
    provider_base_template_refresh_required,
)

sha=current_provider_base_template_sha256()

stale={
    'provider_base_store':{
        'authoring_version':CLEAN_RECONSTRUCTION_AUTHORING_VERSION-1,
        'template_sha256':'deadbeef',
    },
    'providers':{
        'demo':{
            'base_source':CLEAN_RECONSTRUCTION_SOURCE,
            'clean_reconstruction_verified':True,
            'clean_reconstruction_authoring_version':CLEAN_RECONSTRUCTION_AUTHORING_VERSION-1,
            'provider_base_template_sha256':'deadbeef',
            'base_sha256':'deadbeef',
        }
    }
}
assert provider_base_template_refresh_required(stale) is True

current={
    'provider_base_store':{
        'authoring_version':CLEAN_RECONSTRUCTION_AUTHORING_VERSION,
        'template_sha256':sha,
    },
    'providers':{
        'demo':{
            'base_source':CLEAN_RECONSTRUCTION_SOURCE,
            'clean_reconstruction_verified':True,
            'clean_reconstruction_authoring_version':CLEAN_RECONSTRUCTION_AUTHORING_VERSION,
            'provider_base_template_sha256':sha,
            'base_sha256':sha,
        }
    }
}
assert provider_base_template_refresh_required(current) is False

print('ProviderBase exact-template identity contract passed')
