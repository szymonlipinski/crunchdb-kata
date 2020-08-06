Database storage.
=================

Basic assumptions:
------------------

* the list of the questions will not change
* there are two kinds of questions: single choice and multiple choice
* the kind of question will not change
* there is a strict set of values a user can choose from
* the set of choices will not change
* the user's answer for multi choice question can contain only ``yes/no/not_answered``
* the three answers values will not change


Implementation Details
======================

There are three main command line scripts. All are fully configurable from the command line. All the options
should be described with the ``--help`` argument:

* ``acquisition.py`` - for loading the jsonl files to the MongoDB
* ``storage.py`` - for loading the data from the MongoDB to the storage disk files
* ``query.py`` - for querying the stored data

Other files and directories:

* ``storage_dir`` - the default storage directory, currently filled with sample data
* ``common`` - directory with common python code for all the three scripts
* ``data`` - original directory with the original scripts for generating the data
* ``data/data.tar.bz2`` - packed *.jsonl files used to generate the ``storage_dir`` data
* ``database`` - main python package with the logic for storing the data on disk
* ``database/test`` - tests for the storage functionality
* ``database/sample_files`` - sample configuration files for testing different config files corruption
* ``database/db.py`` - the storage interface used to read and write the data files
* ``database/file_format.py`` - internal implementation of writing and reading the storage data file formats

Additional notes:

* There is no locking of the scripts, so it's possible that race conditions could do some bad things
  when running that in parallel, but it was going to be a simple implementation.

The MongoDB Data
=================

The MongoDB data is modified a little bit:

* The ``"_id"`` field is filled with the ``"pk"`` value.
* There is a new field ``"_fetched"`` set to False, which is later set to True by the storage.py script
  to avoid fetching the same data again.

Data Format
===========

Physical Storage
----------------

* All the data is stored in files in one directory.
* There is a basic config file ``"config.json"``, with the whole storage configuration.
* Each of the answers is named ``"collection"``.
* For each collection there are two kinds of data files:

  * for SingleValue collection: ``<collection>.single.data``
  * for MultiValue collection: ``<collection>.multi.data``

* For each collection there is also a file ``<collection>.ids``, with a list of ``user_id`` values,
  which is used to prevent of loading the same answer again.


Config File Format
~~~~~~~~~~~~~~~~~~

In the data directory, there is a basic config file ``"config.json"`` in the format of:

.. code-block:: json

    {
        "choices": {
            "carbrands": [
              "ac", "ac propulsion"
            ],
            "singers": [
              "10cc", "2pac", "50_cent"
            ]
        },
        "collections": {
            "listened_singers": {
                "multiple_answers": true,
                "choices": "singers"
            }
        }
    }

Data File Format
~~~~~~~~~~~~~~~~

The data file format depends on the number of possible replies.

We have the list of possible choices to choose from in the config file.
Here, in the data files, we store only the indices of the answers.

Single Reply Data File Format
*****************************

In case of just one reply, the format of one answer is:


.. code-block::

    -------------------------------
    |   4B     |         2B       |
    | user_id  | chosen_answer_id |
    -------------------------------

- ``user_id``: is an integer with the id of the user preferences
- ``chosen_answer_id``: is an integer with the answer index read from the config file

Multiple Replies Data File Format
*********************************

In case of multiple answers, the format is:

.. code-block::

    -----------------------------------------------------------------------
    |   4B     |           varies            |           varies           |
    | user_id  | chosen_yes_answer_bit_field | chosen_no_answer_bit_field |
    -----------------------------------------------------------------------


- ``user_id``: is an integer with the id of the user preferences
- ``chosen_yes_answer_bit_field``: is a bitset, where each set bit means user answered ``'yes'`` to the choice at this index
- ``chosen_no_answer_bit_field``: is a bitset, where each set bit means user answered ``'no'`` to the choice at this index

The ``not_answered`` choices are not stored as they can be calculated from the stored values.
It would be enough to make binary and of ``chosen_yes_answer_bit_field`` and ``chosen_no_answer_bit_field`` and check
all the bits which are not set.

Estimated Memory Requirements
*****************************

A randomly generated answer for the list of listened to singers has 95kB.
There are 556 singers in the sample list.
Storing 556 bits require 70B (as we would need to save whole bytes to a file).

Storing this kind of answer from one user would require:

.. code-block::

    pk:                            4B
    chosen_yes_answer_bit_field:  70B
    chosen_no_answer_bit_field:   70B
                    -----------------
                          total: 144B


Storing data for 1k user answers would require:

.. code-block::

    raw answer:  92MiB
    data file:  140KiB
    -------------------
         ratio: 0.1%

Real Memory Requirements
************************

The script ``data/generate_data.py`` generated 1005 jsonl files (95KiB on average).
There are 1k files loaded, which gives about 93MiB of data.

The total size of the data stored on disk is:

.. code-block::

    ids files:    35KB
    data files:  650KB
    config file:  12KB
    -------------------
    total:       697KB

The data size ratio is 0.7%.

The Data Format Drawbacks
*************************

- There is no update of the data possible.
- The preferences for a ``pk`` can be loaded only once.
- There is no data paging, so it would be difficult to create an index
  (unless we index the exact byte position in a file, which can be not so efficient).
- Currently, every search requires a full sequential scan.

Benchmarks
==========

I've generated 10,005 jsonl files.
The size of the directory is 1018MB.

Loading the files to MongoDB with ``make acquire`` took about 22s.

Loading the data form the MongoDB to the storage with ``make storage`` took about 340s.

The storage files sizes are:

.. code-block::

            file type         |    number of options   | file extension |  file size
    ----------------------------------------------------------------------------------
      index file              |        10k of integers |          .ids  |     40 KB
      single answer data file |        556 [singers]   |  .single.data  |     59 KB
      single answer data file |        271 [carbrands] |  .single.data  |     59 KB
      multi answer data file  |        556 [singers]   |   .multi.data  |    1.4 MB
      multi answer data file  |        271 [carbrands] |   .multi.data  |    704 KB

The total directory size is 7 MB.

Querying Speed
--------------

The querying time depends if the size of the data (so the kind of the file and the size of potential choices).

All the current queries need to make the same kind of a sequential scan on one data file,
prepare an internal data with names and counts for all the choices,
and then sort and return the first one or three (I have added one more query to the list:
``"What are the three least known music artist?"``).

So, the algorithm is the same, the difference is just in the data.

As you can see, for the single answer files, the times are the same, as we store exactly 6B for each answer,
regardless the amount of choices.

For the multi answer files, there is twice more work to do with bits for the singers data than for the carbrands.
That's why there is twice the time.


.. code-block::

            file type         |    number of options   |   query time
    ----------------------------------------------------------------------------------
      single answer data file |        556 [singers]   |     0.01 ms
      single answer data file |        271 [carbrands] |     0.01 ms
      multi answer data file  |        556 [singers]   |     0.88 ms
      multi answer data file  |        271 [carbrands] |     0.41 ms

Testing
========

Quickcheck
----------

I wanted to use quickcheck for random tests arguments.
However, there is a bug for the pytest quickcheck, which made it a little bit problematic.
https://bitbucket.org/pytest-dev/pytest-quickcheck/issues/15/randomize-marker-doesnt-work

Makefile Commands
=================

There is a Makefile with the following commands:

* `make acquire` - runs the `acquisition.py` with default arguments
* `make storage` - runs the `storage.py` with default arguments
* `make query`   - runs the `query.py` with default arguments
* `make check`   - runs the `flake8` for basic checks
* `make clean`   - runs the `black` formatter
* `make test`    - runs the `pytest` with 5 threads
