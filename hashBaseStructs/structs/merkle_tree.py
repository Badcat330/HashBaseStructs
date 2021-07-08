import hashlib


class MerkleTreeNode(object):
        def __init__(self, key, hash, value=None):
            self.key = key
            self.hash = hash
            self.value = value
            self.left_children = None
            self.right_children = None

class MerkleTree(object):
    
    def __init__(self, hash_type='sha256', is_data_storable=True):

        if hash_type in ['tiger', 'blake3']:
            pass
        # elif ['sha256', 'md5', 'sha224', 'sha384', 'sha512', 'sha1', 'blake2b', 'blake2s'
        #                 'sha3_256', 'sha3_224', 'sha3_384', 'sha3_512', 'shake_128', 'shake_256']:
        else:
            # TODO: handle exception if accure 
            self.hash_function = getattr(hashlib, hash_type)
        self.clear()

    def clear(self):
        self.root = None
        self.leaves_count = 0

    def add_range(self, keys: list, values: list):
        pass

    def get_changeset(self, destination):
        pass

    def swap(self, other_tree):
        pass

    def __delitem__(self, key):
        pass
    
    def __getitem__(self, key):
        pass
    
    def __setitem__(self, key, value):
        pass

    def swap(self, other):
        pass

    def __len__(self):
        return self.leaves_count

    def __contains__(self, item):
        pass

    def __eq__(self, o: object) -> bool:
        return super().__eq__(o)

    def __ne__(self, o: object) -> bool:
        return super().__ne__(o)

    