from interface.definitions import MCDAProblem, Alternative, Criterion
import numpy as np
from utils.matrice_tools import apply_on_each_index, apply_on_each_element


class MCDAProxy(object):
    def __init__(self, problem):
        self.problem = problem

    def apply_on_each_crit(self, func):
        x_dim = len(self.problem.alternativesList)
        y_dim = len(self.problem.alternativesList[0].criteriaList) if x_dim > 0 else 0

        result = np.zeros((x_dim, y_dim))

        for x in range(x_dim):
            for y in range(y_dim):
                result[x, y] = func(self.problem.alternativesList[x].criteriaList[y])

        return result

    def alt_count(self):
        return len(self.problem.alternativesList)

    def crit_count(self):
        return len(self.problem.alternativesList[0].criteriaList) if self.alt_count() > 0 else 0

    def criterion(self, i, j):
        if i >= self.alt_count() or j >= self.crit_count():
            raise ValueError('index out of bounds')

        return self.problem.alternativesList[i].criteriaList[j]

    def weight(self, i):
        return self.problem.criteria_weights[i]

    def value(self, i, j):
        return self.criterion(i, j).value

    def direction(self, i):
        return self.criterion(i, j).minmax

    def p(self, i):
        return self.problem.criteria_preference[i]

    def q(self, i):
        return self.problem.criteria_indifference[i]

    def veto(self, i):
        return self.problem.veto_thresholds[i]


def electre_is(problem):
    assert isinstance(problem, MCDAProblem), "This metod works only with MCDAproblems"

    pr = MCDAProxy(problem)

    def js(a, b):
        def predicate(j):
            return pr.value(a, j) >= pr.value(b, j) - pr.q(j)

        indexes = filter(predicate, range(pr.crit_count()))
        return list(indexes)

    def jq(a, b):
        def predicate(j):
            return pr.value(b, j) - pr.p(j) <= pr.value(a, j) < pr.value(b, j) - pr.q(j)

        indexes = filter(predicate, range(pr.crit_count()))
        return list(indexes)

    def jp(a, b):
        def predicate(j):
            return pr.value(b, j) > pr.value(a, j) + pr.p(j)

        indexes = filter(predicate, range(pr.crit_count()))
        return list(indexes)

    def fi(a, b, j):
        nom = pr.p(j) + pr.value(a, j) - pr.value(b, j)
        denom = pr.p(j) - pr.q(j)
        return float(nom)/denom

    def concordance(a, b):
        if len(jp(a, b)) == pr.crit_count():
            return 0
        if len(js(a, b)) == pr.crit_count():
            return 1

        part1 = sum(pr.weight(j) for j in js(a, b))

        part2 = sum(fi(a, b, j) * pr.weight(j) for j in jq(a, b))

        norm = sum(pr.weight(j) for j in range(pr.crit_count()))

        return float(part1 + part2) / norm

    s = 0.9
    dim = pr.alt_count()
    concordance_mtx = apply_on_each_index(concordance, (dim, dim))

    def condition1(val):
        return 0.5 < val < s

    def filter_by_condition(value):
        if condition1(value):
            return value

        return None

    filtered_matrix = apply_on_each_element(filter_by_condition, concordance_mtx)
    print(filtered_matrix)

    def condition2(a, b, j):
        def w(a, b, j):
            norm = sum(pr.weight(j) for j in range(pr.crit_count()))
            nom = 1 - concordance_mtx[a, b] - pr.weight(j) / norm
            denom = 1 - s - pr.weight(j) / norm
            return float(nom) / denom

        return pr.value(a, j) + pr.veto(j) >= pr.q(j) + w(a, b, j)

    def filter2(a, b):
        return all(condition2(a, b, j) for j in range(pr.crit_count()))

    filtered2_matrix = apply_on_each_index(filter2, (dim, dim))
    print(filtered2_matrix)


def main():
    problem = MCDAProblem()

    alt1 = Alternative("test1", 0, [
        Criterion(200),
        Criterion(10),
        Criterion(0.1),
        Criterion(5),
    ])

    alt2 = Alternative("test1", 0, [
        Criterion(150),
        Criterion(20),
        Criterion(0.5),
        Criterion(1),
    ])

    alt3 = Alternative("test1", 0, [
        Criterion(250),
        Criterion(15),
        Criterion(1),
        Criterion(3),
    ])

    problem.alternativesList = [alt1, alt2, alt3]
    problem.criteria_weights = [0.2, 0.3, 0.4, 0.1]
    problem.criteria_preference = [10., 2., 0.2, 1.7]
    problem.criteria_indifference = [5., 1., 0.1, 0.6]
    problem.veto_thresholds = [500, 100, 10, 50]

    electre_is(problem)


if __name__ == '__main__':
    main()
