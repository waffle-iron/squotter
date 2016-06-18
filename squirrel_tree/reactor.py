"""Reactor: the object containing callbacks for trie."""
from abc import ABCMeta, abstractmethod


class Reactor(object):

    """Reactor interface."""

    __metaclass__ = ABCMeta

    @abstractmethod
    def delete_callback(self, parent, suffix):
        """
        Called when a terminal key is completely removed.

        :param parent: The parent of suffix to be removed
        :param key:  The suffix which is removed.
        :return: nothing
        """

    @abstractmethod
    def insert_callback(self, chain, value):
        """
        Called when a value is inserted into a Trie.

        :param chain: list of relative keys under which value is inserted
        :param value: the value being inserted
        """

    @abstractmethod
    def create_callback(self, chain):
        """
        Called when a subtrie for new key is created.

        :param chain: the chain of parent keys, ending with the key of created
        Trie
        """

    @abstractmethod
    def move_callback(self, old_chain, old_key, new_chain, new_key):
        """
        Called when a subtree is moved.

        :param old_chain: the old location of the subtree
        :param old_key: the key of subtree under old location
        :param new_chain: the new location of the subtree
        :param key: the key of subtree under new location
        """


class EmptyReactor(Reactor):

    """Reactor which does nothing."""

    def delete_callback(self, parent, suffix):
        """Do nothing."""
        pass

    def insert_callback(self, chain, value):
        """Do nothing."""
        pass

    def create_callback(self, chain):
        """Do nothing."""
        pass

    def move_callback(self, old_chain, old_key, new_chain, new_key):
        """Do nothing."""
        pass
