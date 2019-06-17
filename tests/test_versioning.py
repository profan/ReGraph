import networkx as nx

from regraph import NetworkXHierarchy

from regraph.audit import VersionedGraph, VersionedHierarchy
from regraph.rules import Rule
from regraph import primitives


class TestVersioning(object):
    """Class for testing `regraph.audit` module."""

    def __init__(self):
        graph = nx.DiGraph()
        graph.add_nodes_from(["circle", "square"])
        graph.add_edge("circle", "square")
        self.initial_graph = graph

    def test_graph_rollback(self):
        g = VersionedGraph(self.initial_graph)

        # Branch 'test'
        g.branch("test")

        pattern = nx.DiGraph()
        pattern.add_node("square")
        rule = Rule.from_transform(pattern)
        # _, rhs_clone =
        rule.inject_clone_node("square")
        g.rewrite(
            rule, {"square": "square"},
            "Clone square")

        # Switch to master
        g.switch_branch("master")

        # Add edge and triangle
        pattern = nx.DiGraph()
        pattern.add_nodes_from(["circle"])
        rule = Rule.from_transform(pattern)
        # _, rhs_clone =
        rule.inject_add_edge("circle", "circle")
        rule.inject_add_node("triangle")
        rule.inject_add_edge("triangle", "circle")
        rhs_instance, _ = g.rewrite(
            rule, {"circle": "circle"},
            "Add edge to circle and triangle")
        triangle = rhs_instance["triangle"]

        # Clone circle
        pattern = nx.DiGraph()
        pattern.add_node("circle")
        rule = Rule.from_transform(pattern)
        _, rhs_clone = rule.inject_clone_node("circle")

        rhs_instance, rollback_commit = g.rewrite(
            rule, {"circle": "circle"},
            "Clone circle")

        # Remove original circle
        pattern = nx.DiGraph()
        pattern.add_node("circle")
        rule = Rule.from_transform(pattern)
        rule.inject_remove_node("circle")

        rhs_instance, _ = g.rewrite(
            rule,
            {"circle": rhs_instance["circle"]},
            message="Remove circle")

        # Merge circle clone and triangle
        pattern = nx.DiGraph()
        pattern.add_nodes_from(["circle", "triangle"])
        rule = Rule.from_transform(pattern)
        rule.inject_merge_nodes(["circle", "triangle"])

        rhs_instance, _ = g.rewrite(
            rule,
            {
                "circle": rhs_instance[rhs_clone],
                "triangle": triangle
            },
            message="Merge circle and triangle")

        # print("\n")
        # print(g._deltas["test"]["rule"])

        g.rollback(rollback_commit)

        g.merge_with("test")

        # primitives.print_graph(g.graph)

    def test_networkx_hierarchy_versioning(self):
        """Test hierarchy versioning functionality."""
        hierarchy = NetworkXHierarchy()
        shapes = nx.DiGraph()
        primitives.add_nodes_from(
            shapes, ["c", "s"])
        hierarchy.add_graph("shapes", shapes)

        colors = nx.DiGraph()
        primitives.add_nodes_from(
            colors, ["w", "b"])
        hierarchy.add_graph("colors", colors)

        ag = nx.DiGraph()
        primitives.add_nodes_from(
            ag, ["wc", "bc", "ws", "bs"])
        hierarchy.add_graph("ag", ag)

        nugget = nx.DiGraph()
        primitives.add_nodes_from(
            nugget, ["wc1", "wc2", "bc1", "ws1", "bs2"])
        hierarchy.add_graph("nugget", nugget)

        hierarchy.add_typing(
            "ag", "shapes", {
                "wc": "c",
                "bc": "c",
                "ws": "s",
                "bs": "s"
            })
        hierarchy.add_typing(
            "ag", "colors", {
                "wc": "w",
                "bc": "b",
                "ws": "w",
                "bs": "b"
            })
        hierarchy.add_typing(
            "nugget", "ag", {
                "wc1": "wc",
                "wc2": "wc",
                "bc1": "bc",
                "ws1": "ws",
                "bs2": "bs"
            })
        hierarchy.add_typing(
            "nugget", "colors", {
                "wc1": "w",
                "wc2": "w",
                "bc1": "b",
                "ws1": "w",
                "bs2": "b"
            })

        base = nx.DiGraph()
        base.add_nodes_from(["node"])
        hierarchy.add_graph("base", base)
        hierarchy.add_typing(
            "colors",
            "base", {
                "w": "node",
                "b": "node"
            })

        h = VersionedHierarchy(hierarchy)

        h.branch("test1")

        pattern = nx.DiGraph()
        pattern.add_nodes_from(["s"])
        rule2 = Rule.from_transform(pattern)
        rule2.inject_remove_node("s")

        h.rewrite(
            "shapes",
            rule2, {"s": "s"},
            message="Remove square")

        h.switch_branch("master")

        pattern = nx.DiGraph()
        pattern.add_nodes_from(["wc"])

        rule1 = Rule.from_transform(pattern)
        rule1.inject_clone_node("wc")

        h.rewrite(
            "ag",
            rule1, {"wc": "wc"},
            message="Clone 'wc'")

        pattern = nx.DiGraph()
        pattern.add_nodes_from(["wc1"])

        rule3 = Rule.from_transform(pattern)
        rule3.inject_add_node("new_node")
        rule3.inject_add_edge("new_node", "wc1")

        h.rewrite("nugget", rule3, {"wc1": "wc1"})

        h.switch_branch("test1")
        h.switch_branch("master")

        print(h._deltas["test1"])
        for g, r in h._deltas["test1"]["rule_hierarchy"]["rules"].items():
            print(g)
            print(r)
        h.merge_with("test1")

        print("-------> Nugget")
        primitives.print_graph(h.hierarchy.graph["nugget"])
        print("\n")
        print("-------> AG")
        primitives.print_graph(h.hierarchy.graph["ag"])
        print("\n")
        print("-------> Colors")
        primitives.print_graph(h.hierarchy.graph["colors"])
        print("\n")
        print("-------> shapes")
        primitives.print_graph(h.hierarchy.graph["shapes"])
        print("\n")
        print("-------> base")
        primitives.print_graph(h.hierarchy.graph["base"])
        print("\n")
