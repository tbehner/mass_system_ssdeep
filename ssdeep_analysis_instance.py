from mass_client import FileAnalysisClient
from common_analysis_ssdeep import CommonAnalysisSsdeep
import logging

debug_logger = logging.getLogger('debug')

class SsdeepAnalysisInstance(FileAnalysisClient):
    def __init__(self, config_object):
        super(SsdeepAnalysisInstance, self).__init__(config_object)
        self.samples_endpoint = config_object['GLOBAL']['ServerURL'] + 'api/sample/'
        self.ssdeep_sample_relation_endpoint = config_object['GLOBAL']['ServerURL'] + 'api/sample_relation/submit_ssdeep/'
        self.cache = dict()
        self._load_cache()
        self.ssdeep_analysis = CommonAnalysisSsdeep(self.cache)

    def _load_cache(self):
        samples_page = {'next': self.samples_endpoint}
        while samples_page['next']:
            next_page_url = samples_page['next']
            samples_page = self.http_client.get(next_page_url).json()
            for sample in samples_page['results']:
                if sample['_cls'].startswith('Sample.FileSample'):
                    self.cache[sample['url']] = sample['ssdeep_hash']

    def post_new_ssdeep_relation(self, sample_url, other_url, value):
        data = {
                'sample': sample_url,
                'other': other_url,
                'match': value
                }
        response = self.http_client.post_json(self.ssdeep_sample_relation_endpoint, data=data)
        if response.status_code != 201:
            debug_logger.error('Could not post ssdeep sample relation')
            debug_logger.error(response.text)

    def do_analysis(self, analysis_request):
        report = self.ssdeep_analysis.analyze_string(self.sample_dict['ssdeep_hash'], self.sample_dict['url'])
        for identifier, value in report['similar samples']:
            self.post_new_ssdeep_relation(self.sample_dict['url'], identifier, value)
        self.submit_report(
            analysis_request['url'],
            additional_metadata={'number_of_similar_samples': len(report['similar samples'])}

            )
