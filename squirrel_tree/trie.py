"""Basic implemntation of a trie, with callbacks."""

import collections
from os.path import commonprefix

from .reactor import EmptyReactor


class Trie(collections.MutableMapping):

    """
    Implementation of Trie.

    API:

    Trie.root -- key for this Trie
    Trie.terminal -- True if has no sub-Tries
    Trie[key] -- get value for this Trie and sub-Tries
    """

    def __init__(self, parent=None, suffix=None, reactor=None):
        """
        Create a new trie.

        :param parent: Parent of this trie. By default root trie is created.
        :param suffix: Suffix of this trie w/respect to the parent. By default
               empty string. Should be non-empty if parent is given.
        :param reactor: Implementation of squirrel_trie.Reactor. Trie
               operations will call the corresponding callbacks of the reactor.
               By default squirrel_trie.EmptyReactor.
        """
        # Key this Trie node represents w/respect to its parent
        self._suffix = suffix or ''
        self._parent = parent
        if not len(self._suffix) and self._parent:
            raise ValueError("Only root trie may have empty suffix.")
        # Sub-tries for this Trie node, indexed by their suffixes
        self._subtries = {}
        # Callback reactor
        self._reactor = reactor or EmptyReactor()
        # Content of this node
        self._content = None
        self._has_content = False
        self._reactor.create_callback(self.chain)

    @property
    def chain(self):
        """
        Return the chain of keys to this trie.

        :return: The list containing sub-keys for all the tries from the root
        to this trie.
        """
        if self._parent:
            return self._parent.chain + [self._suffix]
        else:
            return [self._suffix]

    @property
    def has_content(self):
        """
        Check if this trie has a value assigned to it.

        :return: True if there's a value assigned for the key of this trie,
        False otherwise.
        """
        return self._has_content

    @property
    def terminal(self):
        """
        Check if trie is a terminal trie.

        :return: True if it contains no sub-tries, False otherwise.
        """
        return len(self._subtries) == 0

    def get_subtrie(self, rkey):
        """
        Get subtrie of this trie, corresponding to the given relative key.

        :param rkey: relative subkey
        :return: subtrie corresponding to the given subkey
        """
        return self._subtries[rkey]

    def __getitem__(self, key):
        return self._get_relative(key)

    def _get_relative(self, rkey):
        # If relative key is empty string, it's for the content of this node
        if rkey == '':
            if not self.has_content:
                raise KeyError("No content in requested key (get).")
            return self._content

        prefix, length = self._find_containing_prefix(rkey)
        return self._subtries[prefix][rkey[length:]]

    def _find_containing_prefix(self, rkey):
        best = self._find_best_prefix(rkey)
        if not best:
            raise KeyError("No requested key.")
        prefix, length = best
        if len(prefix) != length:
            raise KeyError("No requested key.")
        return prefix, length

    def _find_best_prefix(self, rkey):
        for prefix in self._subtries.keys():
            common = commonprefix([prefix, rkey])
            if common:
                return prefix, len(common)
        return None

    def __setitem__(self, key, value):
        self._set_relative(key, value)

    def _set_relative(self, rkey, value):
        # If relative key is empty string, it's for the content of this node
        if rkey == '':
            self._content = value
            self._has_content = True
            self._reactor.insert_callback(self.chain, value)
        else:
            # Now we have four possibilities:
            # 1. There's no subtrie with overlapping key
            # 2. There's subtrie with key which starts with rkey
            # 3. There's subtrie with key which is a start of rkey
            # 4. There's subtrie with overlapping key
            best = self._find_best_prefix(rkey)
            if not best:
                # Possibility 1
                self._add_in_new_subtrie(rkey, value)
            else:
                prefix, length = best
                if length == len(prefix):
                    # Possibility 2
                    self._subtries[prefix][rkey[length:]] = value
                elif length == len(rkey):
                    # Possibility 3
                    self._add_over_subtree(rkey, value, prefix)
                else:
                    # Possibility 4
                    self._add_intersecting(rkey, value, prefix, length)

    def _add_in_new_subtrie(self, rkey, value):
        new_subtrie = Trie(parent=self, suffix=rkey, reactor=self._reactor)
        self._subtries[rkey] = new_subtrie
        new_subtrie[''] = value

    def _add_over_subtree(self, rkey, value, prefix):
        # First add a new subtrie
        self._add_in_new_subtrie(rkey, value)
        self._move_subtree_down(prefix, rkey)

    def _move_subtree_down(self, prefix, where_to):
        subtrie = self._subtries[prefix]
        new_prefix = prefix[len(where_to):]
        new_parent = self._subtries[where_to]
        subtrie.move(new_parent, new_prefix)
        del self._subtries[prefix]
        self._reactor.move_callback(self.chain, prefix,
                                    new_parent.chain, new_prefix)

    def move(self, parent, suffix):
        """
        Move this subtree to become a child of a given parent.

        :param parent: New parent.
        :param suffix: Suffix with respect to new parent.
        :return: nothing
        """
        self._parent = parent
        self._suffix = suffix
        self._parent.register_child(self, suffix)

    def register_child(self, child, suffix):
        """
        Register a trie as a child.

        :param child: A trie to add as a child.
        :param suffix: Suffix to use for a child.
        """
        assert suffix not in self._subtries
        self._subtries[suffix] = child

    def unregister_child(self, suffix):
        """
        Remove a child tree.

        :param suffix: Suffix for the child to be removed.
        """
        assert suffix in self._subtries
        del self._subtries[suffix]
        self._compact()

    def _add_intersecting(self, rkey, value, prefix, length):
        # First add a new subtrie
        intersection = rkey[:length]
        assert intersection == prefix[:length]
        assert intersection not in self._subtries
        intersection_subtrie = Trie(parent=self, suffix=intersection,
                                    reactor=self._reactor)
        self._subtries[intersection] = intersection_subtrie
        # Now move another subtrie under it
        self._move_subtree_down(prefix, intersection)
        # And proceed with adding value
        intersection_subtrie[rkey[length:]] = value

    def __delitem__(self, key):
        self._del_relative(key)

    def _del_relative(self, rkey):
        # If relative key is empty string, it's for the content of this node
        if rkey == '':
            if not self._has_content:
                raise KeyError("No content in requested key (del).")
            self._has_content = False
            self._reactor.delete_callback(self.chain, self._content)
            self._content = None
            self._compact()
        else:
            prefix, length = self._find_containing_prefix(rkey)
            del self._subtries[prefix][rkey[length:]]

    def _compact(self):
        if self.has_content:
            # Do not compact trie with content
            return
        if self._suffix == '':
            # Do not compact the root
            return
        if len(self._subtries) == 0:
            # No content and no subtries => just remove this trie
            self._reactor.remove_callback(self.chain)
            self._parent.unregister_child(self._suffix)
        elif len(self._subtries) == 1:
            # No content, one child only. We need to join this trie with
            # the child.
            suffix = self._subtries.keys()[0]
            child = self._subtries[suffix]
            new_suffix = self._suffix + suffix
            child.move(self._parent, new_suffix)
            self._reactor.move_callback(self.chain, suffix,
                                        self._parent.chain, new_suffix)
            self._reactor.remove_callback(self.chain)
            self._parent.unregister_child(self._suffix)

    def __iter__(self):
        raise NotImplementedError

    def __len__(self):
        total = 1
        for _, child in self._subtries.items():
            total += len(child)
        return total
