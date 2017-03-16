import sys
import time
import logging
import configparser
from mass_client import AnalysisClient
from common_analysis_ssdeep import CommonAnalysisSsdeep
from mass_api_client.resources import Sample, SsdeepSampleRelation
from common_helper_files import update_config_from_env

logging.basicConfig()
log = logging.getLogger('ssdeep_analysis_system')
log.setLevel(logging.INFO)

class SsdeepAnalysisInstance(AnalysisClient):
    def __init__(self, **kwargs):
        self.cache = dict()
        self._load_cache()
        self.ssdeep_analysis = CommonAnalysisSsdeep(self.cache)
        super().__init__(**kwargs)

    def _load_cache(self):
        start_time = time.time()
        for sample in Sample.items():
            if sample._class_identifier.startswith('Sample.FileSample'):
                self.cache[sample.id] = sample.ssdeep_hash
        log.info('Finished building cache in {}sec. Size {} bytes.'.format(time.time() - start_time, sys.getsizeof(self.cache)))

    def analyze(self, scheduled_analysis):
        sample = scheduled_analysis.get_sample()
        report = self.ssdeep_analysis.analyze_string(sample.ssdeep_hash, sample.id)

        for identifier, value in report['similar samples']:
            SsdeepSampleRelation.create(sample, Sample.get(identifier), match=value)

        self.submit_report(
            scheduled_analysis,
            json_report_objects={'ssdeep_report': {'number_of_similar_samples': len(report['similar samples'])}},
            )


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')
    update_config_from_env(config)
    SsdeepAnalysisInstance.create_from_config(config).start()
