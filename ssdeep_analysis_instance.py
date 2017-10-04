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
log = logging.getLogger('ssdeep_analysis_system')
log.setLevel(logging.INFO)

class SsdeepAnalysisInstance():
    def __init__(self):
        self.cache = dict()
        self._load_cache()
        self.ssdeep_analysis = CommonAnalysisSsdeep(self.cache)

    def _load_cache(self):
        log.info('Start loading cache...')
        start_time = time.time()
        for sample in Sample.items():
            if sample._class_identifier.startswith('Sample.FileSample'):
                self.cache[sample.id] = sample.ssdeep_hash
        log.info('Finished building cache in {}sec. Size {} bytes.'.format(time.time() - start_time, sys.getsizeof(self.cache)))

    def analyze(self, scheduled_analysis):
        sample = scheduled_analysis.get_sample()
        log.info('Analysing {}'.format(sample))
        report = self.ssdeep_analysis.analyze_string(sample.ssdeep_hash, sample.id)

        for identifier, value in report['similar samples']:
            SsdeepSampleRelation.create(sample, Sample.get(identifier), match=value)

        scheduled_analysis.create_report(
            additional_metadata={'number_of_similar_samples': len(report['similar samples'])},
            )


if __name__ == "__main__":
    mass_api_client.ConnectionManager().register_connection(
        'default', 
        'IjU5ZDM3Yzc0NmFlY2RmN2MzNGIzYjAyMiI.WhU92Ly9Tq4fc63l0qKfl944Jj4', 
        'http://localhost:8000/api/', 
        timeout=6
        )

    analysis_system_instance = utils.get_or_create_analysis_system_instance(identifier='ssdeep',
                                                                      verbose_name= 'ssdeep similarity analysis',
                                                                      tag_filter_exp='sample-type:filesample',
                                                                      )
    ssdeep_ana = SsdeepAnalysisInstance()
    utils.process_analyses(analysis_system_instance, ssdeep_ana.analyze, sleep_time=3)
