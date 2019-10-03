"""The Rancho objects to be sold."""


class Rancho:
    """Ranchos are a modern rebranding of Tarantulas."""

    def __init__(self, species, description, stock=0):
        """Init Rancho object.

        species: String
        description: String
        Stock: Int
        """
        self.species = species
        self.description = description
        self.stock = stock
