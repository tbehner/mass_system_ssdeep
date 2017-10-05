import os
import sys
import time
import logging
import configparser
from common_analysis_ssdeep import CommonAnalysisSsdeep
from common_helper_files import update_config_from_env
import mass_api_client
from mass_api_client.resources import Sample, SsdeepSampleRelation
from mass_api_client import utils

logging.basicConfig()
logger = logging.getLogger('ssdeep_analysis_system')
logger.setLevel(logging.INFO)

class SsdeepAnalysisInstance():
    def __init__(self):
        self.cache = dict()
        self._load_cache()
        self.ssdeep_analysis = CommonAnalysisSsdeep(self.cache)

    def _load_cache(self):
        logger.info('Start loading cache...')
        start_time = time.time()
        for sample in Sample.items():
            if not 'file' in sample.unique_features.keys():
                continue
            self.cache[sample.id] = sample.unique_features['file']['ssdeep_hash']
        logger.info('Finished building cache in {}sec. Size {} bytes.'.format(time.time() - start_time, sys.getsizeof(self.cache)))

    def analyze(self, scheduled_analysis):
        sample = scheduled_analysis.get_sample()
        logger.info('Analysing {}'.format(sample))
        if not 'file' in sample.unique_features.keys():
            logger.info('This is not a file sample: {}'.format(sample))
            report = {'error': 'This sample has no unique_feature "file".'}

        report = self.ssdeep_analysis.analyze_string(sample.unique_features['file']['ssdeep_hash'], sample.id)

        # for identifier, value in report['similar samples']:
            # SsdeepSampleRelation.create(sample, Sample.get(identifier), match=value)

        scheduled_analysis.create_report(
            additional_metadata={'number_of_similar_samples': len(report['similar samples'])},
            )


if __name__ == "__main__":
    api_key = os.getenv('MASS_API_KEY', '')
    logger.info('Got API KEY {}'.format(api_key))
    server_addr = os.getenv('MASS_SERVER', 'http://localhost:8000/api/')
    logger.info('Connecting to {}'.format(server_addr))
    timeout = int(os.getenv('MASS_TIMEOUT', '60'))
    mass_api_client.ConnectionManager().register_connection('default', api_key, server_addr, timeout=timeout)

    analysis_system_instance = utils.get_or_create_analysis_system_instance(identifier='ssdeep',
                                                                      verbose_name= 'ssdeep similarity analysis',
                                                                      tag_filter_exp='sample-type:filesample',
                                                                      )
    ssdeep_ana = SsdeepAnalysisInstance()
    utils.process_analyses(analysis_system_instance, ssdeep_ana.analyze, sleep_time=3)
