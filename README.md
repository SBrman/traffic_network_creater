## Contains representations of different graph theoretic objects. 
## Graphs can be created using the data given in the .\data folder
## Sumo networks, demands, trips, routes and turn proportions can be generated using the Graph object. Those files can be directly used with the SUMO simulator.

### Network Definition
Consider the digraph, $G = (V, E)$. Set of all nodes, $V$ and the set of all edges is given by $E = E_{r} \cup E_{h} \cup E_{s}$. Here, $E_{r}$, $E_{h}$ and $E_{s}$ are the set of on-ramp, highway and off-ramp links. For node $v$ denote the sets of incoming and outgoing links with 
$\Gamma^-(v) = \left\lbrace (i, j): v=j ~\forall (i, j) \in E \right\rbrace$ 
and $\Gamma^+(v) = \left\lbrace (i, j): v=i ~\forall (i, j) \in E \right\rbrace$ 
respectively. For link $e = (i, j)$ denote the sets of incoming and outgoing links with 
$\mathcal{I}(i, j) = \Gamma^{-}(i)$ and $\mathcal{O}(i, j) = \Gamma^{+}(j)$ respectively. 
Let, $M = \bigcup\limits_{v \in V} M_v$ where the set of moves for a node, $v$ is 
$M_v = \Gamma^-(v) \times \Gamma^+(v)$.
