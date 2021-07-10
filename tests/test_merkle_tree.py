import pytest
from hashBaseStructs.structs.merkle_tree import MerkleTree

@pytest.fixture(scope="function")
def tree_source():
    return MerkleTree()

@pytest.fixture(scope="function")
def tree_destination():
    return MerkleTree()

def test_basic(tree_source, tree_destination):
    assert len(tree_source) == 0
    assert len(tree_destination) == 0