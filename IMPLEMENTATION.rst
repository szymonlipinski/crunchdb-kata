Database storage.
=================

Basic assumptions:
------------------

- the list of questions will not change
- there are two kind of questions: one choice and multiple choice
- the kind of question will not change
- there is a strict set of values a user can choice from
- the set of choices will not change
- the user's answer for multi choice question can contain only `yes/no/not_answered`
- the three answers values will not change

Physical Storage
----------------

- All the data is stored in files in one directory.
- There is a basic config file `"config.json"` with the whole storage configuration.
- Each of the answers is named `"collection"`.
- For each collection there are two kinds of data files:
    - for SingleValue collection: `<collection>.single.data`
    - for MultiValue collection: `<collection>.multi.data`
- For each collection there is also a file `<collection>.ids` with a list of `user_id` which is used to check of an answer is not loaded again.


Config File Format
~~~~~~~~~~~~~~~~~~

In the data directory, there is a basic config file "config.json" in the format of:

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

One Reply Data File Format
**************************

In case of just one reply, the format is:


.. code-block::

    -------------------------------
    |   4B     |         2B       |
    | user_id  | chosen_answer_id |
    -------------------------------

- `user_id`: is an integer with the id of the user preferences
- `chosen_answer_id`: is an integer with the answer id read from the config file

Multiple Replies Data File Format
*********************************

In case of multiple answers, the format is:

.. code-block::

    -----------------------------------------------------------------------
    |   4B     |           varies            |           varies           |
    | user_id  | chosen_yes_answer_bit_field | chosen_no_answer_bit_field |
    -----------------------------------------------------------------------


- `user_id`: is an integer with the id of the user preferences
- `chosen_answer_bit_field`: is a bit set where each set bit means user answered 'yes' to the choice at this index
- `chosen_no_answer_bit_field`: is a bit set where each set bit means user answered 'no' to the choice at this index

The `not_answered` choices are not stored as they can be calculated from the stored values,
they are the positions where both: chosen_yes_answer_bit_field and chosen_no_answer_bit_field
have unset bits.

Estimated Memory Requirements
*****************************

A randomly generated answer for the list of listened to singers has 95kB.
There are 556 singers in the sample list.
Storing 556 bits require 70B.

Storing answer from one user would require:

.. code-block::

    user_id:                       4B
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

The script `data/generate_data.py` generated 1005 jsonl files (95KiB on average).
There are 1k files loaded, which gives about 93MiB of data.

The total size of the data stored on disk is:

.. code-block::

    ids files:    35KiB
    data files:  650KiB
    config file:  12KiB
    ---------------
    total:       697 KiB

The data size ratio is 0.7%.


The Data Format Drawbacks
*************************

- There is no update of the data possible.
- The preferences for a `user_id` can be loaded only once.
- There is no data paging, so it would be difficult to create an index.
- Every search currently requires a full sequential scan.


Testing
========

Quickcheck
----------

I wanted to use quickcheck for random tests arguments.
However, there is a bug for the pytest quickcheck, which made it a little bit problematic.
https://bitbucket.org/pytest-dev/pytest-quickcheck/issues/15/randomize-marker-doesnt-work
