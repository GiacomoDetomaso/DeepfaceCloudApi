from unittest import TestCase
from unittest.mock import patch

from rules.services import DeepFaceWrapper
from rules.operations import FaceRepresentationUploader, FaceRepresentation
from rules.blobs import ObjectPersistenceManager

class FaceRepresentationUploaderTest(TestCase):
    
    def setUp(self) -> None:
        wrapper = DeepFaceWrapper('data/img14.jpg', 'MTCNN', 'Facenet512')
        emb = wrapper.generate_embeddings()

        with patch.object(ObjectPersistenceManager, 'upload', return_value=True) as opm_upload_mock:
            opm_mock = ObjectPersistenceManager()
    
    
    def tearDown(self) -> None:
        return super().tearDown()