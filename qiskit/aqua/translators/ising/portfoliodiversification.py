# -*- coding: utf-8 -*-

# Copyright 2018 IBM.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================

from collections import OrderedDict

import numpy as np
from qiskit.quantum_info import Pauli
from qiskit.aqua import Operator

def get_portfoliodiversification_qubitops(rho, n, q):
        """Converts an instnance of portfolio optimization into a list of Paulis.

        Args:
            rho (numpy.ndarray) : an asset-to-asset similarity matrix, such as the covariance matrix.
            n (integer) : the number of assets.
            q (integer) : the number of clusters of assets to output.

        Returns:
            operator.Operator: operator for the Hamiltonian.
        """

        #N = (n + 1) * n  # number of qubits
        N = n**2 + n

        A = np.max(np.abs(rho)) * 1000  # A parameter of cost function

        # Determine the weights w
        instance_vec = rho.reshape(n ** 2)

        # quadratic term Q
        q0 = np.zeros([N,1])
        Q1 = np.zeros([N,N])
        Q2 = np.zeros([N,N])
        Q3 = np.zeros([N, N])

        for x in range(n**2,n**2+n):
            q0[x] = 1

        Q0 = A*np.dot(q0,q0.T)
        for ii in range(0,n):
            v0 = np.zeros([N,1])
            for jj in range(n*ii,n*(ii+1)):
                v0[jj] = 1
            Q1 = Q1 + np.dot(v0,v0.T)
        Q1 = A*Q1

        for jj in range(0,n):
            v0 = np.zeros([N,1])
            v0[n*jj+jj] = 1
            v0[n**2+jj] = -1
            Q2 = Q2 + np.dot(v0, v0.T)
        Q2 = A*Q2


        for ii in range(0, n):
            for jj in range(0,n):
                Q3[ii*n + jj, n**2+jj] = -0.5
                Q3[n ** 2 + jj,ii * n + jj] = -0.5


        Q3 = A * Q3

        Q = Q0+Q1+Q2+Q3

        # linear term c:
        c0 = np.zeros(N)
        c1 = np.zeros(N)
        c2 = np.zeros(N)
        c3 = np.zeros(N)

        for x in range(n**2):
            c0[x] = instance_vec[x]
        for x in range(n**2,n**2+n):
            c1[x] = -2*A*q
        for x in range(n**2):
            c2[x] = -2*A
        for x in range(n**2):
            c3[x] = A

        g = c0+c1+c2+c3

        # constant term r
        c = A*(q**2 + n)

        # Defining the new matrices in the Z-basis

        Iv = np.ones(N)
        Qz = (Q / 4)
        gz = (-g / 2 - np.dot(Iv, Q / 4) - np.dot(Q / 4, Iv))
        cz = (c + np.dot(g / 2, Iv) + np.dot(Iv, np.dot(Q / 4, Iv)))

        cz = cz + np.trace(Qz)
        Qz = Qz - np.diag(np.diag(Qz))

        # Getting the Hamiltonian in the form of a list of Pauli terms

        pauli_list = []
        for i in range(N):
            if gz[i] != 0:
                wp = np.zeros(N)
                vp = np.zeros(N)
                vp[i] = 1
                pauli_list.append((gz[i], Pauli(vp, wp)))
        for i in range(N):
            for j in range(i):
                if Qz[i, j] != 0:
                    wp = np.zeros(N)
                    vp = np.zeros(N)
                    vp[i] = 1
                    vp[j] = 1
                    pauli_list.append((2 * Qz[i, j], Pauli(vp, wp)))

        pauli_list.append((cz, Pauli(np.zeros(N), np.zeros(N))))
        return Operator(paulis=pauli_list)

def get_portfoliodiversification_solution(rho, n, q, result):
        """Tries to obtain a feasible solution (in vector form) of an instnance of portfolio diversification from the results dictionary.

    Args:
        rho (numpy.ndarray) : an asset-to-asset similarity matrix, such as the covariance matrix.
        n (integer) : the number of assets.
        q (integer) : the number of clusters of assets to output.
        result (dictionary) : a dictionary obtained by QAOA.run or VQE.run containing key 'eigvecs'.

    Returns:
        x_state (numpy.ndarray) : a vector describing the solution.
        """

        v = result['eigvecs'][0]
        # N = (n + 1) * n  # number of qubits
        N = n ** 2 + n
        
        index_value = [x for x in range(len(v)) if v[x] == max(v)][0]
        string_value = "{0:b}".format(index_value)

        while len(string_value)<N:
            string_value = '0'+string_value

        x_state = list()
        for elements in string_value:
            if elements == '0':
                x_state.append(0)
            else:
                x_state.append(1)

        x_state = np.flip(x_state, axis=0)

        return x_state

def get_portfoliodiversification_value(rho, n, q, x_state):
    """Evaluates an objective function of an instnance of portfolio diversification and its solution (in vector form).

    Args:
        rho (numpy.ndarray) : an asset-to-asset similarity matrix, such as the covariance matrix.
        n (integer) : the number of assets.
        q (integer) : the number of clusters of assets to output.
        x_state (numpy.ndarray) : a vector describing the solution.

    Returns:
        float: cost of the solution.
    """

    # N = (n + 1) * n  # number of qubits
    N = n ** 2 + n

    A = np.max(np.abs(rho)) * 1000  # A parameter of cost function

    # Determine the weights w
    instance_vec = rho.reshape(n ** 2)

    # quadratic term Q
    q0 = np.zeros([N, 1])
    Q1 = np.zeros([N, N])
    Q2 = np.zeros([N, N])
    Q3 = np.zeros([N, N])

    for x in range(n ** 2, n ** 2 + n):
        q0[x] = 1

    Q0 = A * np.dot(q0, q0.T)
    for ii in range(0, n):
        v0 = np.zeros([N, 1])
        for jj in range(n * ii, n * (ii + 1)):
            v0[jj] = 1
        Q1 = Q1 + np.dot(v0, v0.T)
    Q1 = A * Q1

    for jj in range(0, n):
        v0 = np.zeros([N, 1])
        v0[n * jj + jj] = 1
        v0[n ** 2 + jj] = -1
        Q2 = Q2 + np.dot(v0, v0.T)
    Q2 = A * Q2

    for ii in range(0, n):
        for jj in range(0, n):
            Q3[ii * n + jj, n ** 2 + jj] = -0.5
            Q3[n ** 2 + jj, ii * n + jj] = -0.5

    Q3 = A * Q3

    Q = Q0 + Q1 + Q2 + Q3

    # linear term c:
    c0 = np.zeros(N)
    c1 = np.zeros(N)
    c2 = np.zeros(N)
    c3 = np.zeros(N)

    for x in range(n ** 2):
        c0[x] = instance_vec[x]
    for x in range(n ** 2, n ** 2 + n):
        c1[x] = -2 * A * q
    for x in range(n ** 2):
        c2[x] = -2 * A
    for x in range(n ** 2):
        c3[x] = A

    g = c0 + c1 + c2 + c3

    # constant term r
    c = A * (q ** 2 + n)

    # Evaluates the cost distance from a binary representation
    fun = lambda x: np.dot(np.around(x), np.dot(Q, np.around(x))) + np.dot(g, np.around(x)) + c

    return fun(x_state)