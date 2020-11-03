from collections import OrderedDict
from enum import Enum
import joblib
import numpy as np
from ptype.utils import project_root


TYPE_INDEX = 0
MISSING_INDEX = 1
ANOMALIES_INDEX = 2


def _get_unique_vals(col, return_counts=False):
    """List of the unique values found in a column."""
    return np.unique([str(x) for x in col.tolist()], return_counts=return_counts)


# Use same names and values as the constants in Model.py. Could consolidate.
class _Status(Enum):
    TYPE = 1
    MISSING = 2
    ANOMALOUS = 3


class _Feature(Enum):
    U_RATIO = 5
    U_RATIO_CLEAN = 6
    U = 7
    U_CLEAN = 8


class Column:
    def __init__(self, series, counts, p_t, p_z):
        self.series = series
        self.p_t = p_t
        self.p_t_canonical = {}
        self.p_z = p_z
        self.type = self.inferred_type()
        self.unique_vals, self.unique_vals_counts = _get_unique_vals(self.series, return_counts=True)
        self._initialise_missing_anomalies()
        features = self._get_features(counts)
        self.arff_type = _column2ARFF.get_arff(features)[0]
        self.arff_posterior = _column2ARFF.get_arff(features)[1]
        self.categorical_values = (
            self.get_normal_values() if self.arff_type == "nominal" else None
        )

    def __repr__(self):
        return repr(self.__dict__)

    def _initialise_missing_anomalies(self):
        row_posteriors = self.p_z[self.type]
        max_row_posterior_indices = np.argmax(row_posteriors, axis=1)

        self.normal_indices = list(np.where(max_row_posterior_indices == TYPE_INDEX)[0])
        self.missing_indices = list(np.where(max_row_posterior_indices == MISSING_INDEX)[0])
        self.anomalous_indices = list(np.where(max_row_posterior_indices == ANOMALIES_INDEX)[0])

    def inferred_type(self):
        """Get most likely inferred type for the column."""
        return max(self.p_t, key=self.p_t.get)

    def get_normal_ratio(self):
        """Get proportion of unique values in the column which are considered neither anomalous nor missing."""
        return round(sum(self.unique_vals_counts[self.normal_indices]) / sum(self.unique_vals_counts), 2)

    def get_missing_ratio(self):
        """Get proportion of unique values in the column which are considered 'missing'."""
        return round(sum(self.unique_vals_counts[self.missing_indices]) / sum(self.unique_vals_counts), 2)

    def get_anomalous_ratio(self):
        """Get proportion of unique values in the column which are considered 'anomalous'."""
        return round(sum(self.unique_vals_counts[self.anomalous_indices]) / sum(self.unique_vals_counts), 2)

    def get_normal_values(self):
        """Get list of all values in the column which are considered neither anomalous nor missing."""
        return list(self.unique_vals[self.normal_indices])

    def get_missing_values(self):
        """Get a list of the values in the column which are considered 'missing'."""
        return list(self.unique_vals[self.missing_indices])

    def get_anomalous_values(self):
        """Get a list of the values in the column which are considered 'anomalous'."""
        return list(self.unique_vals[self.anomalous_indices])

    def reclassify(self, new_t):
        """Assign a different type to the column, and adjust the interpretation of missing/anomalous values
        accordingly.

        :param new_t: the new type, which must be one of the types known to ptype.
        """
        if new_t not in self.p_z:
            raise Exception(f"Type {new_t} is unknown.")
        self.type = new_t
        self._initialise_missing_anomalies()
        # update the arff types?

    def _get_features(self, counts):
        posterior = OrderedDict()
        for t, p in sorted(self.p_t.items()):
            # aggregate date subtypes
            t_0 = t.split("-")[0]
            if t_0 in posterior.keys():
                posterior[t_0] += p
            else:
                posterior[t_0] = p
        posterior = posterior.values()

        entries = [str(int_element) for int_element in self.series.tolist()]
        U = len(np.unique(entries))
        U_clean = len(self.normal_indices)

        N = len(entries)
        N_clean = sum([counts[index] for index in self.normal_indices])

        u_ratio = U / N
        if U_clean == 0 and N_clean == 0:
            u_ratio_clean = 0.0
        else:
            u_ratio_clean = U_clean / N_clean

        return np.array(list(posterior) + [u_ratio, u_ratio_clean, U, U_clean])


class _Column2ARFF:
    def __init__(self, model_folder="models"):
        self.normalizer = joblib.load(model_folder + "robust_scaler.pkl")
        self.clf = joblib.load(model_folder + "LR.sav")

    def get_arff(self, features):
        features[[_Feature.U.value, _Feature.U_CLEAN.value]] = self.normalizer.transform(
            features[[_Feature.U.value, _Feature.U_CLEAN.value]].reshape(1, -1)
        )[0]
        arff_type = self.clf.predict(features.reshape(1, -1))[0]

        if arff_type == "categorical":
            arff_type = "nominal"
        # find normal values for categorical type

        arff_type_posterior = self.clf.predict_proba(features.reshape(1, -1))[0]

        return arff_type, arff_type_posterior


_column2ARFF = _Column2ARFF(project_root() + "/../models/")
