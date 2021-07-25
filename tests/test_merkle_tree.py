import pytest
import random
from hashBaseStructs.structs.merkle_tree import MerkleTree

def data_generator(seed, length, max_number):
    random.seed(seed)
    data = []
    for i in range(length):
        item = random.randrange(-max_number, max_number)
        data.append((i, item))

    random.shuffle(data)
    return data


@pytest.fixture(scope="function", params=[
    (15, 10, 100),
    (25, 100, 1000)
])
def data_fixture(request):
    seed = request.param[0]
    length = request.param[1]
    max_number = request.param[2]
    data = data_generator(seed, length, max_number)
    return data

@pytest.fixture(scope="function")
def tree():
    return MerkleTree()

@pytest.fixture(scope="function", params=[
    (15, 10, 100),
    (25, 100, 1000)
])
def two_trees_with_data(request):
    tree_source = MerkleTree()
    tree_destination = MerkleTree()
    seed = request.param[0]
    length = request.param[1]
    max_number = request.param[2]
    data = data_generator(seed, length, max_number)
    
    for i in range(0, length):
        if i % 2 == 0:
            tree_source[data[i][0]] = data[i][1]
        else:
            tree_destination[data[i][0]] = data[i][1]

    return {"Source": tree_source, "Destination": tree_destination}

# Basic tests
def test_basic(tree):
    assert len(tree) == 0

# Test CRUD functionality
def test_set_get(tree, data_fixture):
    for item in data_fixture:
        tree[item[0]] = item[1]

    random.shuffle(data_fixture)

    for item in data_fixture:
        assert tree[item[0]] == item[1]
    
    assert len(tree) == len(data_fixture)

def test_add_range(tree, data_fixture):
    keys = []
    values = []
    
    for item in data_fixture:
        keys.append(item[0])
        values.append(item[1])
    
    tree.add_range(keys, values)

    random.shuffle(data_fixture)

    for item in data_fixture:
        assert tree[item[0]] == item[1]

    assert len(tree) == len(data_fixture)

def test_update(tree, data_fixture):
    keys = []
    values = []
    
    for item in data_fixture:
        keys.append(item[0])
        values.append(item[1])
    
    tree.add_range(keys, values)

    random.shuffle(values)

    for value, key in zip(values, keys):
        tree[key] = value
        assert len(tree) == len(data_fixture)
        assert tree[key] == value

def test_contain(tree, data_fixture):
    for item in data_fixture:
        tree[item[0]] = item[1]

    random.shuffle(data_fixture)

    for item in data_fixture:
        assert item[0] in tree

def test_delite(tree,  data_fixture):
    for item in data_fixture:
        tree[item[0]] = item[1]

    random.shuffle(data_fixture)

    for item in data_fixture:
        del tree[item[0]]
        assert not item[0] in tree
    
    assert len(tree) == 0

# Test methodth for CDC 
def test_eq(two_trees_with_data):
    tree_source = two_trees_with_data["Source"]
    tree_destination = two_trees_with_data["Destination"]

    assert tree_source == tree_source
    assert not tree_source == tree_destination

    assert not tree_source != tree_source
    assert tree_source!= tree_destination

def test_changeset():
    tree_source = MerkleTree()
    tree_destination = MerkleTree()

    tree_source.add_range([2, 7, 12, 15, 16, 17, 25], [1, 2, 3, 4, 5, 6, 7])
    tree_destination.add_range([8, 15, 18, 21], [1, 2, 3, 4])

    print(tree_source.get_changeset(tree_destination))

# Test help methodth
def test_swap(data_fixture):
    tree_source = MerkleTree()
    tree_destination = MerkleTree()

    for i in range(0, len(data_fixture)):
        if i % 2 == 0:
            tree_source[data_fixture[i][0]] = data_fixture[i][1]
        else:
            tree_destination[data_fixture[i][0]] = data_fixture[i][1]

    tree_source.swap(tree_destination)

    for i in range(0, len(data_fixture)):
        if i % 2 == 0:
            assert tree_destination[data_fixture[i][0]] == data_fixture[i][1]
        else:
            assert tree_source[data_fixture[i][0]] == data_fixture[i][1]

def test_clear(tree, data_fixture):
    for item in data_fixture:
        tree[item[0]] = item[1]

    tree.clear()

    assert len(tree) == 0


# Test hashes
@pytest.mark.parametrize("hash", [
    "blake2s",
    "blake2b",
    "blake3",
    'tigerhash'
])
def test_blake3(hash, data_fixture):
    tree_source = MerkleTree(hash)
    tree_destination = MerkleTree(hash)
    
    for i in range(0, len(data_fixture)):
        if i % 2 == 0:
            tree_source[data_fixture[i][0]] = data_fixture[i][1]
        else:
            tree_destination[data_fixture[i][0]] = data_fixture[i][1]

    assert tree_source == tree_source
    assert not tree_source == tree_destination

