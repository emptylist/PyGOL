"""
A cellular automaton simulator, designed to operate in a
topological, abstract manner, as inspired by the Clojure
version presented in Clojure Programming, by Chas Emerick
et al.

My goal in building this is primarily as an exercise to expand
my understanding of both Python and Clojure, and to see how well
I can build interesting and powerful abstractions using OO
tools, particularly without desperately fighting the language.
"""

# Cells

class Cell(object):
    """
    The Cell is the fundamental building block of a Cellular
    Automaton, as one might expect.  We want Cells to be unique
    and identifiable (though not necessarily explicitly).  The
    simplest way to express this in a coordinate-free fashion is
    to have each cell be a simple object.

    This should allow us to set up a fairly powerful abstraction,
    but it at least appears to come at a price: this approach tends
    toward mutation (which will surely cause trouble if not carefully
    contained), and involves a bit of boilerplate.
    """

    def __init__(self, inital_state = Dead):
        self._state = initial_state
        self._new_state = None
    """
    Simplest first.  Getters and setters for the status.  While this
    might smell of corporate Java style, the getters and setters serve a
    purpose and show, if not a weakness, then a trade-off made in Python.
    As a dynamic language, we can't (as far as I know!) create an enum
    type for the status field.  Thus making self._status private-by-convention
    and using setters and getters is to make up for the lack of strong types.
    Notably, this trade-off is also present in Clojure, which is simply ignored
    in the GoL example.  Thus, while we have some boilerplate here, it is
    not entirely fair to compare this extra code to the short Clojure example.
    """
    @property
    def state(self):
        return self._state

    @state.set
    def alive(self):
        self._state = "Alive"

    @state.set
    def dead(self):
        self._state = "Dead"

    """
    Unfettered mutation, however, will play havok when trying to work
    with the cells at a more functional, abstract level (i.e. if we try to
    use map or a similar idiom).  So we'll build our own pseudo-transactional
    apparatus (the alternative is deep copies of the topology, which I may revisit
    as a potentially more functional-looking alternative).  I think this is
    a clear example of a win for immutability and persistence.

    This leaves us with a difficult question: who is responsible for ensuring we
    don't get into a morass of mutability bugs?  Is it the cells themselves?  Is it
    the topology?  The stepper function?  Each present different trade-offs.  Of the
    three, the cells and the stepper seem like the appropriate candidates, especially
    since the topology may not exist independent of the cells, depending on the design.
    The stepper seems like a good option, but then our calling code is dealing with
    implementation details, which makes for poor abstraction.  On the other hand, having
    the cells deal with their own update transactions makes for good abstraction, but
    requires dependency injection.  This isn't bad, per se, but to me, it really does
    point out that our data and our logic are intertwined.
    """

    def transactional_update(self, rule, neighbors_fn):
        if rule(self, neighbors_fn) == "Alive":
            self._new_state = "Alive"
        else:
            self._new_state = "Dead"

    @state.set
    def update(self):
        if self._new_state:
            self._state = self._new_state
            self._new_state = None

    """
    Okay, so we're saying that we're going to have to inject a rule function and
    the neighbor set.  This method also implies that the topology will live at a level
    above the cells themselves, rather than being defined implicitly by giving each
    cell a list of neighbors.  While involving more moving parts, this avoids cyclic
    references, which seems more problematic to me than adding a topology layer.

    The downside here is that we have to make two passes over the topology's data
    structure when we go to update the world.  Once to compute the new state, and again
    to actually do the update.  At the very least, this means the implementation of the
    cells is leaking into the topology layer, although we can hopefully stem the abstraction
    leak there.
    """

# Topology

"""
Okay, now we want to think about the topology itself.  Much like in the
Clojure solution, we want to step back and think about what that means.
Mathematically, the core concept of a topology (in point-set topology, anyway),
is that attached to any point, there exists a collection of open sets that form
the neighborhoods of that point.  For our discrete case, we really only care about
the smallest non-trivial neighborhood, i.e. the set of neighbors of each cell.

Thus, we can really think of a topology as a function that takes a cell and returns
a set of cells: the neighbors of that cell.  Of course, there's an obvious Python
construct that does this: a dictionary.  But then we're back to dealing with a specific
implementation. In fact, while it's more general than using an array (or lists),
using a dictionary implies a specific and finite topology.  What if we wanted an infinite
set?

So really, the topology should act like a function, or, since we're in a OO language,
supply an interface that obeys that function's contract.

Okay, I'm not even going to pretend we're solving this in an FP manner.  Let's play Object
Hierarchy.
"""

class AbstractTopology(object):
    def __init__(self):
        raise NotImplementedError

    def find_neighbors(self, cell):
        raise NotImplementedError

    @property
    def cells(self):
        return self._cells

"""
Yup, it's an entirely virtual class, serving as nothing more than a template for what
promises that a real Topology should fulfill.  I wonder if I've got some sort of C++
infection when I write things like this, but I'm at a loss for how to proceed.
"""

class PlaneTopology(AbstractTopology):
    def __init__(self, height, width, initial_live_cells = None):
        self._height = height
        self._width = width
        self._cells = [Cell() for i in xrange(self._height * self._width)]
        if initial_live_cells:
            for (row, column) in initial_live_cells:
                self._cells[row * self._width + column].alive()

    def find_neighbors(self, cell):
        neighbors = []
        flat_index = self._cells.index(cell)
        row = flat_index % self._width
        column = flat_index - (row * self._width)
        for i in [-1, 1]:
            for j in [-1, 1]:
                neighbor_row = row + i
                neighbor_column = column + j
                if (neighbor_row >= 0) and (neighbor_column >= 0):
                    neighbors.append(self._cells[neighbor_row * self._width + neighbor_column])
        return neighbors

    @property
    def cells(self):
        return self._cells

    @property
    def formatted_cells(self):
        pass

def stepper(topology, rule):
    def step_function(steps):
        for step in xrange(steps):
            for cell in topology.cells:
                cell.transactional_update(rule, topology.find_neighbors)
            for cell in cells:
                cell.update()
    return step_function

def conway_rule(cell, neighbor_fn):
    living_neighbors = len([neighbor.status for neighbor in neighbor_fn(cell)])
    if cell.status = "Alive":
        if living_neighbors < 2:
            return "Dead"
        elif living_neighbors > 3:
            return "Dead"
        else:
            return "Alive"
    else: # cell.status = "Dead"
        if living_neighbors == 3:
            return "Alive"
        else:
            return "Dead"

"""
One notable design choice here in the stepper (and relatedly, in the AbstractTopology class)
is that the cells and topology are both required to be passed to the stepper function.
One could easily concieve that the topology and the list of cells would be bundled together,
and indeed one obvious way to do this (what I might even consider the standard OO approach)
would be to have the topology act as a data structure for the cells.  This is very reasonable,
and is even implemented in the PlaneTopology class, which actually makes passing topology.cells
and topology both to stepper redundant.  However, if we wanted the topology to be able to
generate neighbor cells is some algorithmic manner (as we might need for an infinite structure),
then it's not clear that the topology should be responsible for 'knowing' the structure of
the cells.

I'm open to debate on this, and I'm not sure this isn't an unnecessary (or perhaps just
ineffective) attempt to decouple logically coupled pieces.  In part, this makes me think
this is an example of when OO has strong, and different, opinions from an FP approach.
"""
