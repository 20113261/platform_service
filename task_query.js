db.Task.find({
    "queue": "file_downloader",
    "finished": 0,
    "running": 0,
}).sort({
    "priority": -1,
    "used_times": 1,
    "utime": 1
}).limit(50000).explain("executionStats");

db.Task.find({
    "running": 1,
    "utime": {
        "$lte": "2017-09-30T05:40:01.688Z"
    }
}).limit(10000).explain("executionStats");

db.Task.update({"running": 1, "utime": {"$lte": new Date(new Date().getTime() - 2 * 60 * 60 * 1000)}}, {
    $set: {
        "running": 0,
        "finished": 0,
        "used_times": 0
    }
}, {"multi": true});

// 用于清空大于 maxSecsRunning 的 query
// kills long running ops in MongoDB (taking seconds as an arg to define "long")
// attempts to be a bit safer than killing all by excluding replication related operations
// and only targeting queries as opposed to commands etc.
killLongRunningOps = function (maxSecsRunning) {
    currOp = db.currentOp();
    for (oper in currOp.inprog) {
        op = currOp.inprog[oper - 0];
        if (op.secs_running > maxSecsRunning && op.op == "query" && !op.ns.startsWith("local")) {
            print("Killing opId: " + op.opid
                + " running over for secs: "
                + op.secs_running);
            db.killOp(op.opid);
        }
    }
};


db.Task.find({
    "queue": "file_downloader",
    "finished": 0,
    "running": 0,
    "used_times": {
        "$lte": 6
    }
}).sort({
    "priority": -1,
    "used_times": 1,
    "utime": 1
}).limit(5000).explain("executionStats");


var result = {
    "queryPlanner": {
        "plannerVersion": 1,
        "namespace": "MongoTask.Task",
        "indexFilterSet": false,
        "parsedQuery": {
            "$and": [
                {
                    "used_times": {
                        "$lte": 6
                    }
                },
                {
                    "finished": {
                        "$eq": 0
                    }
                },
                {
                    "queue": {
                        "$eq": "file_downloader"
                    }
                },
                {
                    "running": {
                        "$eq": 0
                    }
                }
            ]
        },
        "winningPlan": {
            "stage": "LIMIT",
            "limitAmount": 0,
            "inputStage": {
                "stage": "KEEP_MUTATIONS",
                "inputStage": {
                    "stage": "FETCH",
                    "filter": {
                        "running": {
                            "$eq": 0
                        }
                    },
                    "inputStage": {
                        "stage": "IXSCAN",
                        "keyPattern": {
                            "queue": 1,
                            "finished": 1,
                            "used_times": 1
                        },
                        "indexName": "queue_1_finished_1_used_times_1",
                        "isMultiKey": false,
                        "direction": "forward",
                        "indexBounds": {
                            "queue": [
                                "[\"file_downloader\", \"file_downloader\"]"
                            ],
                            "finished": [
                                "[0.0, 0.0]"
                            ],
                            "used_times": [
                                "[-inf.0, 6.0]"
                            ]
                        }
                    }
                }
            }
        },
        "rejectedPlans": [
            {
                "stage": "LIMIT",
                "limitAmount": 899,
                "inputStage": {
                    "stage": "FETCH",
                    "inputStage": {
                        "stage": "IXSCAN",
                        "keyPattern": {
                            "queue": 1,
                            "finished": 1,
                            "running": 1,
                            "used_times": 1
                        },
                        "indexName": "queue_1_finished_1_running_1_used_times_1",
                        "isMultiKey": false,
                        "direction": "forward",
                        "indexBounds": {
                            "queue": [
                                "[\"file_downloader\", \"file_downloader\"]"
                            ],
                            "finished": [
                                "[0.0, 0.0]"
                            ],
                            "running": [
                                "[0.0, 0.0]"
                            ],
                            "used_times": [
                                "[-inf.0, 6.0]"
                            ]
                        }
                    }
                }
            },
            {
                "stage": "LIMIT",
                "limitAmount": 956,
                "inputStage": {
                    "stage": "KEEP_MUTATIONS",
                    "inputStage": {
                        "stage": "FETCH",
                        "filter": {
                            "$and": [
                                {
                                    "used_times": {
                                        "$lte": 6
                                    }
                                },
                                {
                                    "finished": {
                                        "$eq": 0
                                    }
                                },
                                {
                                    "running": {
                                        "$eq": 0
                                    }
                                }
                            ]
                        },
                        "inputStage": {
                            "stage": "IXSCAN",
                            "keyPattern": {
                                "queue": 1
                            },
                            "indexName": "queue_1",
                            "isMultiKey": false,
                            "direction": "forward",
                            "indexBounds": {
                                "queue": [
                                    "[\"file_downloader\", \"file_downloader\"]"
                                ]
                            }
                        }
                    }
                }
            },
            {
                "stage": "LIMIT",
                "limitAmount": 903,
                "inputStage": {
                    "stage": "KEEP_MUTATIONS",
                    "inputStage": {
                        "stage": "FETCH",
                        "filter": {
                            "$and": [
                                {
                                    "used_times": {
                                        "$lte": 6
                                    }
                                },
                                {
                                    "queue": {
                                        "$eq": "file_downloader"
                                    }
                                },
                                {
                                    "running": {
                                        "$eq": 0
                                    }
                                }
                            ]
                        },
                        "inputStage": {
                            "stage": "IXSCAN",
                            "keyPattern": {
                                "finished": 1
                            },
                            "indexName": "finished_1",
                            "isMultiKey": false,
                            "direction": "forward",
                            "indexBounds": {
                                "finished": [
                                    "[0.0, 0.0]"
                                ]
                            }
                        }
                    }
                }
            },
            {
                "stage": "LIMIT",
                "limitAmount": 900,
                "inputStage": {
                    "stage": "KEEP_MUTATIONS",
                    "inputStage": {
                        "stage": "FETCH",
                        "filter": {
                            "$and": [
                                {
                                    "finished": {
                                        "$eq": 0
                                    }
                                },
                                {
                                    "queue": {
                                        "$eq": "file_downloader"
                                    }
                                },
                                {
                                    "running": {
                                        "$eq": 0
                                    }
                                }
                            ]
                        },
                        "inputStage": {
                            "stage": "IXSCAN",
                            "keyPattern": {
                                "used_times": 1
                            },
                            "indexName": "used_times_1",
                            "isMultiKey": false,
                            "direction": "forward",
                            "indexBounds": {
                                "used_times": [
                                    "[-inf.0, 6.0]"
                                ]
                            }
                        }
                    }
                }
            }
        ]
    },
    "executionStats": {
        "executionSuccess": true,
        "nReturned": 1000,
        "executionTimeMillis": 3,
        "totalKeysExamined": 1000,
        "totalDocsExamined": 1000,
        "executionStages": {
            "stage": "LIMIT",
            "nReturned": 1000,
            "executionTimeMillisEstimate": 10,
            "works": 1001,
            "advanced": 1000,
            "needTime": 0,
            "needFetch": 0,
            "saveState": 11,
            "restoreState": 11,
            "isEOF": 1,
            "invalidates": 0,
            "limitAmount": 0,
            "inputStage": {
                "stage": "KEEP_MUTATIONS",
                "nReturned": 1000,
                "executionTimeMillisEstimate": 0,
                "works": 1000,
                "advanced": 1000,
                "needTime": 0,
                "needFetch": 0,
                "saveState": 11,
                "restoreState": 11,
                "isEOF": 0,
                "invalidates": 0,
                "inputStage": {
                    "stage": "FETCH",
                    "filter": {
                        "running": {
                            "$eq": 0
                        }
                    },
                    "nReturned": 1000,
                    "executionTimeMillisEstimate": 0,
                    "works": 1000,
                    "advanced": 1000,
                    "needTime": 0,
                    "needFetch": 0,
                    "saveState": 11,
                    "restoreState": 11,
                    "isEOF": 0,
                    "invalidates": 0,
                    "docsExamined": 1000,
                    "alreadyHasObj": 0,
                    "inputStage": {
                        "stage": "IXSCAN",
                        "nReturned": 1000,
                        "executionTimeMillisEstimate": 0,
                        "works": 1000,
                        "advanced": 1000,
                        "needTime": 0,
                        "needFetch": 0,
                        "saveState": 11,
                        "restoreState": 11,
                        "isEOF": 0,
                        "invalidates": 0,
                        "keyPattern": {
                            "queue": 1,
                            "finished": 1,
                            "used_times": 1
                        },
                        "indexName": "queue_1_finished_1_used_times_1",
                        "isMultiKey": false,
                        "direction": "forward",
                        "indexBounds": {
                            "queue": [
                                "[\"file_downloader\", \"file_downloader\"]"
                            ],
                            "finished": [
                                "[0.0, 0.0]"
                            ],
                            "used_times": [
                                "[-inf.0, 6.0]"
                            ]
                        },
                        "keysExamined": 1000,
                        "dupsTested": 0,
                        "dupsDropped": 0,
                        "seenInvalidated": 0,
                        "matchTested": 0
                    }
                }
            }
        },
        "allPlansExecution": [
            {
                "nReturned": 101,
                "executionTimeMillisEstimate": 0,
                "totalKeysExamined": 101,
                "totalDocsExamined": 101,
                "executionStages": {
                    "stage": "LIMIT",
                    "nReturned": 101,
                    "executionTimeMillisEstimate": 0,
                    "works": 101,
                    "advanced": 101,
                    "needTime": 0,
                    "needFetch": 0,
                    "saveState": 11,
                    "restoreState": 11,
                    "isEOF": 0,
                    "invalidates": 0,
                    "limitAmount": 899,
                    "inputStage": {
                        "stage": "FETCH",
                        "nReturned": 101,
                        "executionTimeMillisEstimate": 0,
                        "works": 101,
                        "advanced": 101,
                        "needTime": 0,
                        "needFetch": 0,
                        "saveState": 11,
                        "restoreState": 11,
                        "isEOF": 0,
                        "invalidates": 0,
                        "docsExamined": 101,
                        "alreadyHasObj": 0,
                        "inputStage": {
                            "stage": "IXSCAN",
                            "nReturned": 101,
                            "executionTimeMillisEstimate": 0,
                            "works": 101,
                            "advanced": 101,
                            "needTime": 0,
                            "needFetch": 0,
                            "saveState": 11,
                            "restoreState": 11,
                            "isEOF": 0,
                            "invalidates": 0,
                            "keyPattern": {
                                "queue": 1,
                                "finished": 1,
                                "running": 1,
                                "used_times": 1
                            },
                            "indexName": "queue_1_finished_1_running_1_used_times_1",
                            "isMultiKey": false,
                            "direction": "forward",
                            "indexBounds": {
                                "queue": [
                                    "[\"file_downloader\", \"file_downloader\"]"
                                ],
                                "finished": [
                                    "[0.0, 0.0]"
                                ],
                                "running": [
                                    "[0.0, 0.0]"
                                ],
                                "used_times": [
                                    "[-inf.0, 6.0]"
                                ]
                            },
                            "keysExamined": 101,
                            "dupsTested": 0,
                            "dupsDropped": 0,
                            "seenInvalidated": 0,
                            "matchTested": 0
                        }
                    }
                }
            },
            {
                "nReturned": 44,
                "executionTimeMillisEstimate": 0,
                "totalKeysExamined": 101,
                "totalDocsExamined": 101,
                "executionStages": {
                    "stage": "LIMIT",
                    "nReturned": 44,
                    "executionTimeMillisEstimate": 0,
                    "works": 101,
                    "advanced": 44,
                    "needTime": 57,
                    "needFetch": 0,
                    "saveState": 11,
                    "restoreState": 11,
                    "isEOF": 0,
                    "invalidates": 0,
                    "limitAmount": 956,
                    "inputStage": {
                        "stage": "KEEP_MUTATIONS",
                        "nReturned": 44,
                        "executionTimeMillisEstimate": 0,
                        "works": 101,
                        "advanced": 44,
                        "needTime": 57,
                        "needFetch": 0,
                        "saveState": 11,
                        "restoreState": 11,
                        "isEOF": 0,
                        "invalidates": 0,
                        "inputStage": {
                            "stage": "FETCH",
                            "filter": {
                                "$and": [
                                    {
                                        "used_times": {
                                            "$lte": 6
                                        }
                                    },
                                    {
                                        "finished": {
                                            "$eq": 0
                                        }
                                    },
                                    {
                                        "running": {
                                            "$eq": 0
                                        }
                                    }
                                ]
                            },
                            "nReturned": 44,
                            "executionTimeMillisEstimate": 0,
                            "works": 101,
                            "advanced": 44,
                            "needTime": 57,
                            "needFetch": 0,
                            "saveState": 11,
                            "restoreState": 11,
                            "isEOF": 0,
                            "invalidates": 0,
                            "docsExamined": 101,
                            "alreadyHasObj": 0,
                            "inputStage": {
                                "stage": "IXSCAN",
                                "nReturned": 101,
                                "executionTimeMillisEstimate": 0,
                                "works": 101,
                                "advanced": 101,
                                "needTime": 0,
                                "needFetch": 0,
                                "saveState": 11,
                                "restoreState": 11,
                                "isEOF": 0,
                                "invalidates": 0,
                                "keyPattern": {
                                    "queue": 1
                                },
                                "indexName": "queue_1",
                                "isMultiKey": false,
                                "direction": "forward",
                                "indexBounds": {
                                    "queue": [
                                        "[\"file_downloader\", \"file_downloader\"]"
                                    ]
                                },
                                "keysExamined": 101,
                                "dupsTested": 0,
                                "dupsDropped": 0,
                                "seenInvalidated": 0,
                                "matchTested": 0
                            }
                        }
                    }
                }
            },
            {
                "nReturned": 97,
                "executionTimeMillisEstimate": 0,
                "totalKeysExamined": 101,
                "totalDocsExamined": 101,
                "executionStages": {
                    "stage": "LIMIT",
                    "nReturned": 97,
                    "executionTimeMillisEstimate": 0,
                    "works": 101,
                    "advanced": 97,
                    "needTime": 4,
                    "needFetch": 0,
                    "saveState": 11,
                    "restoreState": 11,
                    "isEOF": 0,
                    "invalidates": 0,
                    "limitAmount": 903,
                    "inputStage": {
                        "stage": "KEEP_MUTATIONS",
                        "nReturned": 97,
                        "executionTimeMillisEstimate": 0,
                        "works": 101,
                        "advanced": 97,
                        "needTime": 4,
                        "needFetch": 0,
                        "saveState": 11,
                        "restoreState": 11,
                        "isEOF": 0,
                        "invalidates": 0,
                        "inputStage": {
                            "stage": "FETCH",
                            "filter": {
                                "$and": [
                                    {
                                        "used_times": {
                                            "$lte": 6
                                        }
                                    },
                                    {
                                        "queue": {
                                            "$eq": "file_downloader"
                                        }
                                    },
                                    {
                                        "running": {
                                            "$eq": 0
                                        }
                                    }
                                ]
                            },
                            "nReturned": 97,
                            "executionTimeMillisEstimate": 0,
                            "works": 101,
                            "advanced": 97,
                            "needTime": 4,
                            "needFetch": 0,
                            "saveState": 11,
                            "restoreState": 11,
                            "isEOF": 0,
                            "invalidates": 0,
                            "docsExamined": 101,
                            "alreadyHasObj": 0,
                            "inputStage": {
                                "stage": "IXSCAN",
                                "nReturned": 101,
                                "executionTimeMillisEstimate": 0,
                                "works": 101,
                                "advanced": 101,
                                "needTime": 0,
                                "needFetch": 0,
                                "saveState": 11,
                                "restoreState": 11,
                                "isEOF": 0,
                                "invalidates": 0,
                                "keyPattern": {
                                    "finished": 1
                                },
                                "indexName": "finished_1",
                                "isMultiKey": false,
                                "direction": "forward",
                                "indexBounds": {
                                    "finished": [
                                        "[0.0, 0.0]"
                                    ]
                                },
                                "keysExamined": 101,
                                "dupsTested": 0,
                                "dupsDropped": 0,
                                "seenInvalidated": 0,
                                "matchTested": 0
                            }
                        }
                    }
                }
            },
            {
                "nReturned": 100,
                "executionTimeMillisEstimate": 0,
                "totalKeysExamined": 101,
                "totalDocsExamined": 101,
                "executionStages": {
                    "stage": "LIMIT",
                    "nReturned": 100,
                    "executionTimeMillisEstimate": 0,
                    "works": 101,
                    "advanced": 100,
                    "needTime": 1,
                    "needFetch": 0,
                    "saveState": 11,
                    "restoreState": 11,
                    "isEOF": 0,
                    "invalidates": 0,
                    "limitAmount": 900,
                    "inputStage": {
                        "stage": "KEEP_MUTATIONS",
                        "nReturned": 100,
                        "executionTimeMillisEstimate": 0,
                        "works": 101,
                        "advanced": 100,
                        "needTime": 1,
                        "needFetch": 0,
                        "saveState": 11,
                        "restoreState": 11,
                        "isEOF": 0,
                        "invalidates": 0,
                        "inputStage": {
                            "stage": "FETCH",
                            "filter": {
                                "$and": [
                                    {
                                        "finished": {
                                            "$eq": 0
                                        }
                                    },
                                    {
                                        "queue": {
                                            "$eq": "file_downloader"
                                        }
                                    },
                                    {
                                        "running": {
                                            "$eq": 0
                                        }
                                    }
                                ]
                            },
                            "nReturned": 100,
                            "executionTimeMillisEstimate": 0,
                            "works": 101,
                            "advanced": 100,
                            "needTime": 1,
                            "needFetch": 0,
                            "saveState": 11,
                            "restoreState": 11,
                            "isEOF": 0,
                            "invalidates": 0,
                            "docsExamined": 101,
                            "alreadyHasObj": 0,
                            "inputStage": {
                                "stage": "IXSCAN",
                                "nReturned": 101,
                                "executionTimeMillisEstimate": 0,
                                "works": 101,
                                "advanced": 101,
                                "needTime": 0,
                                "needFetch": 0,
                                "saveState": 11,
                                "restoreState": 11,
                                "isEOF": 0,
                                "invalidates": 0,
                                "keyPattern": {
                                    "used_times": 1
                                },
                                "indexName": "used_times_1",
                                "isMultiKey": false,
                                "direction": "forward",
                                "indexBounds": {
                                    "used_times": [
                                        "[-inf.0, 6.0]"
                                    ]
                                },
                                "keysExamined": 101,
                                "dupsTested": 0,
                                "dupsDropped": 0,
                                "seenInvalidated": 0,
                                "matchTested": 0
                            }
                        }
                    }
                }
            },
            {
                "nReturned": 101,
                "executionTimeMillisEstimate": 0,
                "totalKeysExamined": 101,
                "totalDocsExamined": 101,
                "executionStages": {
                    "stage": "LIMIT",
                    "nReturned": 101,
                    "executionTimeMillisEstimate": 0,
                    "works": 101,
                    "advanced": 101,
                    "needTime": 0,
                    "needFetch": 0,
                    "saveState": 3,
                    "restoreState": 3,
                    "isEOF": 0,
                    "invalidates": 0,
                    "limitAmount": 899,
                    "inputStage": {
                        "stage": "KEEP_MUTATIONS",
                        "nReturned": 101,
                        "executionTimeMillisEstimate": 0,
                        "works": 101,
                        "advanced": 101,
                        "needTime": 0,
                        "needFetch": 0,
                        "saveState": 3,
                        "restoreState": 3,
                        "isEOF": 0,
                        "invalidates": 0,
                        "inputStage": {
                            "stage": "FETCH",
                            "filter": {
                                "running": {
                                    "$eq": 0
                                }
                            },
                            "nReturned": 101,
                            "executionTimeMillisEstimate": 0,
                            "works": 101,
                            "advanced": 101,
                            "needTime": 0,
                            "needFetch": 0,
                            "saveState": 3,
                            "restoreState": 3,
                            "isEOF": 0,
                            "invalidates": 0,
                            "docsExamined": 101,
                            "alreadyHasObj": 0,
                            "inputStage": {
                                "stage": "IXSCAN",
                                "nReturned": 101,
                                "executionTimeMillisEstimate": 0,
                                "works": 101,
                                "advanced": 101,
                                "needTime": 0,
                                "needFetch": 0,
                                "saveState": 3,
                                "restoreState": 3,
                                "isEOF": 0,
                                "invalidates": 0,
                                "keyPattern": {
                                    "queue": 1,
                                    "finished": 1,
                                    "used_times": 1
                                },
                                "indexName": "queue_1_finished_1_used_times_1",
                                "isMultiKey": false,
                                "direction": "forward",
                                "indexBounds": {
                                    "queue": [
                                        "[\"file_downloader\", \"file_downloader\"]"
                                    ],
                                    "finished": [
                                        "[0.0, 0.0]"
                                    ],
                                    "used_times": [
                                        "[-inf.0, 6.0]"
                                    ]
                                },
                                "keysExamined": 101,
                                "dupsTested": 0,
                                "dupsDropped": 0,
                                "seenInvalidated": 0,
                                "matchTested": 0
                            }
                        }
                    }
                }
            }
        ]
    },
    "serverInfo": {
        "host": "10-10-231-105",
        "port": 27017,
        "version": "3.0.1",
        "gitVersion": "534b5a3f9d10f00cd27737fbcd951032248b5952"
    }
};

db.Task.explain({"queue": "file_downloader", "finished": 0, "running": 0, "used_times": {"$lte": 6}});


db.Task.find({
    "queue": "file_downloader",
    "finished": 0,
    "running": 0,
}).sort({
    "priority": -1,
    "used_times": 1,
    "utime": 1
}).limit(50000).explain("executionStats");

db.Task.update({"running": 1, "utime": {"$lte": new Date(new Date().getTime() - 60 * 60 * 1000)}}, {
    $set: {
        "running": 0,
        "finished": 0,
        "used_times": 0
    }
}, false, true);


db.Task.update({"task_name": "list_hotel_booking_20170929a"}, {"$set": {"utime": new Date(new Date().getTime() - 7 * 24 * 60 * 60 * 1000)}}, false, true);

db.Task.update({"task_name": "list_hotel_booking_20170929a", finished: 0}, {
    $set: {
        "running": 0,
        "finished": 0,
        "used_times": 0
    }
}, false, true);

var log = {
    "queryPlanner": {
        "plannerVersion": 1,
        "namespace": "MongoTask.Task",
        "indexFilterSet": false,
        "parsedQuery": {
            "$and": [
                {
                    "finished": {
                        "$eq": 0
                    }
                },
                {
                    "queue": {
                        "$eq": "file_downloader"
                    }
                },
                {
                    "running": {
                        "$eq": 0
                    }
                }
            ]
        },
        "winningPlan": {
            "stage": "LIMIT",
            "limitAmount": 0,
            "inputStage": {
                "stage": "FETCH",
                "filter": {
                    "$and": [
                        {
                            "finished": {
                                "$eq": 0
                            }
                        },
                        {
                            "queue": {
                                "$eq": "file_downloader"
                            }
                        },
                        {
                            "running": {
                                "$eq": 0
                            }
                        }
                    ]
                },
                "inputStage": {
                    "stage": "IXSCAN",
                    "keyPattern": {
                        "priority": -1,
                        "used_times": 1,
                        "utime": 1
                    },
                    "indexName": "priority_-1_used_times_1_utime_1",
                    "isMultiKey": false,
                    "direction": "forward",
                    "indexBounds": {
                        "priority": [
                            "[MaxKey, MinKey]"
                        ],
                        "used_times": [
                            "[MinKey, MaxKey]"
                        ],
                        "utime": [
                            "[MinKey, MaxKey]"
                        ]
                    }
                }
            }
        },
        "rejectedPlans": [
            {
                "stage": "SORT",
                "sortPattern": {
                    "priority": -1,
                    "used_times": 1,
                    "utime": 1
                },
                "limitAmount": 50000,
                "inputStage": {
                    "stage": "KEEP_MUTATIONS",
                    "inputStage": {
                        "stage": "FETCH",
                        "filter": {
                            "$and": [
                                {
                                    "finished": {
                                        "$eq": 0
                                    }
                                },
                                {
                                    "queue": {
                                        "$eq": "file_downloader"
                                    }
                                }
                            ]
                        },
                        "inputStage": {
                            "stage": "IXSCAN",
                            "keyPattern": {
                                "running": 1,
                                "utime": 1
                            },
                            "indexName": "running_1_utime_1",
                            "isMultiKey": false,
                            "direction": "forward",
                            "indexBounds": {
                                "running": [
                                    "[0.0, 0.0]"
                                ],
                                "utime": [
                                    "[MinKey, MaxKey]"
                                ]
                            }
                        }
                    }
                }
            },
            {
                "stage": "SORT",
                "sortPattern": {
                    "priority": -1,
                    "used_times": 1,
                    "utime": 1
                },
                "limitAmount": 50000,
                "inputStage": {
                    "stage": "KEEP_MUTATIONS",
                    "inputStage": {
                        "stage": "FETCH",
                        "inputStage": {
                            "stage": "IXSCAN",
                            "keyPattern": {
                                "queue": 1,
                                "finished": 1,
                                "running": 1
                            },
                            "indexName": "queue_1_finished_1_running_1",
                            "isMultiKey": false,
                            "direction": "forward",
                            "indexBounds": {
                                "queue": [
                                    "[\"file_downloader\", \"file_downloader\"]"
                                ],
                                "finished": [
                                    "[0.0, 0.0]"
                                ],
                                "running": [
                                    "[0.0, 0.0]"
                                ]
                            }
                        }
                    }
                }
            },
            {
                "stage": "SORT",
                "sortPattern": {
                    "priority": -1,
                    "used_times": 1,
                    "utime": 1
                },
                "limitAmount": 50000,
                "inputStage": {
                    "stage": "KEEP_MUTATIONS",
                    "inputStage": {
                        "stage": "FETCH",
                        "inputStage": {
                            "stage": "IXSCAN",
                            "keyPattern": {
                                "queue": 1,
                                "finished": 1,
                                "running": 1,
                                "used_times": 1
                            },
                            "indexName": "queue_1_finished_1_running_1_used_times_1",
                            "isMultiKey": false,
                            "direction": "forward",
                            "indexBounds": {
                                "queue": [
                                    "[\"file_downloader\", \"file_downloader\"]"
                                ],
                                "finished": [
                                    "[0.0, 0.0]"
                                ],
                                "running": [
                                    "[0.0, 0.0]"
                                ],
                                "used_times": [
                                    "[MinKey, MaxKey]"
                                ]
                            }
                        }
                    }
                }
            }
        ]
    },
    "executionStats": {
        "executionSuccess": true,
        "nReturned": 50000,
        "executionTimeMillis": 254028,
        "totalKeysExamined": 3573396,
        "totalDocsExamined": 3573396,
        "executionStages": {
            "stage": "LIMIT",
            "nReturned": 50000,
            "executionTimeMillisEstimate": 9376,
            "works": 3573398,
            "advanced": 50000,
            "needTime": 3523396,
            "needFetch": 1,
            "saveState": 118681,
            "restoreState": 118681,
            "isEOF": 1,
            "invalidates": 123830,
            "limitAmount": 0,
            "inputStage": {
                "stage": "FETCH",
                "filter": {
                    "$and": [
                        {
                            "finished": {
                                "$eq": 0
                            }
                        },
                        {
                            "queue": {
                                "$eq": "file_downloader"
                            }
                        },
                        {
                            "running": {
                                "$eq": 0
                            }
                        }
                    ]
                },
                "nReturned": 50000,
                "executionTimeMillisEstimate": 9226,
                "works": 3573397,
                "advanced": 50000,
                "needTime": 3523396,
                "needFetch": 1,
                "saveState": 118681,
                "restoreState": 118681,
                "isEOF": 0,
                "invalidates": 123830,
                "docsExamined": 3573396,
                "alreadyHasObj": 0,
                "inputStage": {
                    "stage": "IXSCAN",
                    "nReturned": 3573396,
                    "executionTimeMillisEstimate": 2580,
                    "works": 3573396,
                    "advanced": 3573396,
                    "needTime": 0,
                    "needFetch": 0,
                    "saveState": 118681,
                    "restoreState": 118681,
                    "isEOF": 0,
                    "invalidates": 123830,
                    "keyPattern": {
                        "priority": -1,
                        "used_times": 1,
                        "utime": 1
                    },
                    "indexName": "priority_-1_used_times_1_utime_1",
                    "isMultiKey": false,
                    "direction": "forward",
                    "indexBounds": {
                        "priority": [
                            "[MaxKey, MinKey]"
                        ],
                        "used_times": [
                            "[MinKey, MaxKey]"
                        ],
                        "utime": [
                            "[MinKey, MaxKey]"
                        ]
                    },
                    "keysExamined": 3573396,
                    "dupsTested": 0,
                    "dupsDropped": 0,
                    "seenInvalidated": 0,
                    "matchTested": 0
                }
            }
        },
        "allPlansExecution": [
            {
                "nReturned": 0,
                "executionTimeMillisEstimate": 29667,
                "totalKeysExamined": 3511885,
                "totalDocsExamined": 3511885,
                "executionStages": {
                    "stage": "SORT",
                    "nReturned": 0,
                    "executionTimeMillisEstimate": 29667,
                    "works": 3523496,
                    "advanced": 0,
                    "needTime": 3511885,
                    "needFetch": 11610,
                    "saveState": 118681,
                    "restoreState": 118681,
                    "isEOF": 0,
                    "invalidates": 123817,
                    "sortPattern": {
                        "priority": -1,
                        "used_times": 1,
                        "utime": 1
                    },
                    "memUsage": 32255233,
                    "memLimit": 33554432,
                    "limitAmount": 50000,
                    "inputStage": {
                        "stage": "KEEP_MUTATIONS",
                        "nReturned": 1170178,
                        "executionTimeMillisEstimate": 22946,
                        "works": 3523495,
                        "advanced": 1170178,
                        "needTime": 2341707,
                        "needFetch": 11610,
                        "saveState": 118681,
                        "restoreState": 118681,
                        "isEOF": 0,
                        "invalidates": 123817,
                        "inputStage": {
                            "stage": "FETCH",
                            "filter": {
                                "$and": [
                                    {
                                        "finished": {
                                            "$eq": 0
                                        }
                                    },
                                    {
                                        "queue": {
                                            "$eq": "file_downloader"
                                        }
                                    }
                                ]
                            },
                            "nReturned": 1170178,
                            "executionTimeMillisEstimate": 22836,
                            "works": 3523495,
                            "advanced": 1170178,
                            "needTime": 2341707,
                            "needFetch": 11610,
                            "saveState": 118681,
                            "restoreState": 118681,
                            "isEOF": 0,
                            "invalidates": 123817,
                            "docsExamined": 3511885,
                            "alreadyHasObj": 0,
                            "inputStage": {
                                "stage": "IXSCAN",
                                "nReturned": 3511885,
                                "executionTimeMillisEstimate": 2600,
                                "works": 3511885,
                                "advanced": 3511885,
                                "needTime": 0,
                                "needFetch": 0,
                                "saveState": 118681,
                                "restoreState": 118681,
                                "isEOF": 0,
                                "invalidates": 123817,
                                "keyPattern": {
                                    "running": 1,
                                    "utime": 1
                                },
                                "indexName": "running_1_utime_1",
                                "isMultiKey": false,
                                "direction": "forward",
                                "indexBounds": {
                                    "running": [
                                        "[0.0, 0.0]"
                                    ],
                                    "utime": [
                                        "[MinKey, MaxKey]"
                                    ]
                                },
                                "keysExamined": 3511885,
                                "dupsTested": 0,
                                "dupsDropped": 0,
                                "seenInvalidated": 0,
                                "matchTested": 0
                            }
                        }
                    }
                }
            },
            {
                "nReturned": 0,
                "executionTimeMillisEstimate": 39599,
                "totalKeysExamined": 3520284,
                "totalDocsExamined": 3520284,
                "executionStages": {
                    "stage": "SORT",
                    "nReturned": 0,
                    "executionTimeMillisEstimate": 39599,
                    "works": 3523496,
                    "advanced": 0,
                    "needTime": 3520284,
                    "needFetch": 3211,
                    "saveState": 118681,
                    "restoreState": 118681,
                    "isEOF": 0,
                    "invalidates": 123817,
                    "sortPattern": {
                        "priority": -1,
                        "used_times": 1,
                        "utime": 1
                    },
                    "memUsage": 32335238,
                    "memLimit": 33554432,
                    "limitAmount": 50000,
                    "inputStage": {
                        "stage": "KEEP_MUTATIONS",
                        "nReturned": 3520284,
                        "executionTimeMillisEstimate": 12316,
                        "works": 3523495,
                        "advanced": 3520284,
                        "needTime": 0,
                        "needFetch": 3211,
                        "saveState": 118681,
                        "restoreState": 118681,
                        "isEOF": 0,
                        "invalidates": 123817,
                        "inputStage": {
                            "stage": "FETCH",
                            "nReturned": 3520284,
                            "executionTimeMillisEstimate": 12226,
                            "works": 3523495,
                            "advanced": 3520284,
                            "needTime": 0,
                            "needFetch": 3211,
                            "saveState": 118681,
                            "restoreState": 118681,
                            "isEOF": 0,
                            "invalidates": 123817,
                            "docsExamined": 3520284,
                            "alreadyHasObj": 0,
                            "inputStage": {
                                "stage": "IXSCAN",
                                "nReturned": 3520284,
                                "executionTimeMillisEstimate": 6353,
                                "works": 3520284,
                                "advanced": 3520284,
                                "needTime": 0,
                                "needFetch": 0,
                                "saveState": 118681,
                                "restoreState": 118681,
                                "isEOF": 0,
                                "invalidates": 123817,
                                "keyPattern": {
                                    "queue": 1,
                                    "finished": 1,
                                    "running": 1
                                },
                                "indexName": "queue_1_finished_1_running_1",
                                "isMultiKey": false,
                                "direction": "forward",
                                "indexBounds": {
                                    "queue": [
                                        "[\"file_downloader\", \"file_downloader\"]"
                                    ],
                                    "finished": [
                                        "[0.0, 0.0]"
                                    ],
                                    "running": [
                                        "[0.0, 0.0]"
                                    ]
                                },
                                "keysExamined": 3520284,
                                "dupsTested": 0,
                                "dupsDropped": 0,
                                "seenInvalidated": 0,
                                "matchTested": 0
                            }
                        }
                    }
                }
            },
            {
                "nReturned": 0,
                "executionTimeMillisEstimate": 35677,
                "totalKeysExamined": 3523271,
                "totalDocsExamined": 3523271,
                "executionStages": {
                    "stage": "SORT",
                    "nReturned": 0,
                    "executionTimeMillisEstimate": 35677,
                    "works": 3523496,
                    "advanced": 0,
                    "needTime": 3523271,
                    "needFetch": 224,
                    "saveState": 118681,
                    "restoreState": 118681,
                    "isEOF": 0,
                    "invalidates": 123817,
                    "sortPattern": {
                        "priority": -1,
                        "used_times": 1,
                        "utime": 1
                    },
                    "memUsage": 32568572,
                    "memLimit": 33554432,
                    "limitAmount": 50000,
                    "inputStage": {
                        "stage": "KEEP_MUTATIONS",
                        "nReturned": 3523271,
                        "executionTimeMillisEstimate": 7221,
                        "works": 3523495,
                        "advanced": 3523271,
                        "needTime": 0,
                        "needFetch": 224,
                        "saveState": 118681,
                        "restoreState": 118681,
                        "isEOF": 0,
                        "invalidates": 123817,
                        "inputStage": {
                            "stage": "FETCH",
                            "nReturned": 3523271,
                            "executionTimeMillisEstimate": 7141,
                            "works": 3523495,
                            "advanced": 3523271,
                            "needTime": 0,
                            "needFetch": 224,
                            "saveState": 118681,
                            "restoreState": 118681,
                            "isEOF": 0,
                            "invalidates": 123817,
                            "docsExamined": 3523271,
                            "alreadyHasObj": 0,
                            "inputStage": {
                                "stage": "IXSCAN",
                                "nReturned": 3523271,
                                "executionTimeMillisEstimate": 4090,
                                "works": 3523271,
                                "advanced": 3523271,
                                "needTime": 0,
                                "needFetch": 0,
                                "saveState": 118681,
                                "restoreState": 118681,
                                "isEOF": 0,
                                "invalidates": 123817,
                                "keyPattern": {
                                    "queue": 1,
                                    "finished": 1,
                                    "running": 1,
                                    "used_times": 1
                                },
                                "indexName": "queue_1_finished_1_running_1_used_times_1",
                                "isMultiKey": false,
                                "direction": "forward",
                                "indexBounds": {
                                    "queue": [
                                        "[\"file_downloader\", \"file_downloader\"]"
                                    ],
                                    "finished": [
                                        "[0.0, 0.0]"
                                    ],
                                    "running": [
                                        "[0.0, 0.0]"
                                    ],
                                    "used_times": [
                                        "[MinKey, MaxKey]"
                                    ]
                                },
                                "keysExamined": 3523271,
                                "dupsTested": 0,
                                "dupsDropped": 0,
                                "seenInvalidated": 0,
                                "matchTested": 0
                            }
                        }
                    }
                }
            },
            {
                "nReturned": 101,
                "executionTimeMillisEstimate": 9266,
                "totalKeysExamined": 3523496,
                "totalDocsExamined": 3523496,
                "executionStages": {
                    "stage": "LIMIT",
                    "nReturned": 101,
                    "executionTimeMillisEstimate": 9266,
                    "works": 3523496,
                    "advanced": 101,
                    "needTime": 3523395,
                    "needFetch": 0,
                    "saveState": 118290,
                    "restoreState": 118290,
                    "isEOF": 0,
                    "invalidates": 123817,
                    "limitAmount": 49899,
                    "inputStage": {
                        "stage": "FETCH",
                        "filter": {
                            "$and": [
                                {
                                    "finished": {
                                        "$eq": 0
                                    }
                                },
                                {
                                    "queue": {
                                        "$eq": "file_downloader"
                                    }
                                },
                                {
                                    "running": {
                                        "$eq": 0
                                    }
                                }
                            ]
                        },
                        "nReturned": 101,
                        "executionTimeMillisEstimate": 9116,
                        "works": 3523496,
                        "advanced": 101,
                        "needTime": 3523395,
                        "needFetch": 0,
                        "saveState": 118290,
                        "restoreState": 118290,
                        "isEOF": 0,
                        "invalidates": 123817,
                        "docsExamined": 3523496,
                        "alreadyHasObj": 0,
                        "inputStage": {
                            "stage": "IXSCAN",
                            "nReturned": 3523496,
                            "executionTimeMillisEstimate": 2570,
                            "works": 3523496,
                            "advanced": 3523496,
                            "needTime": 0,
                            "needFetch": 0,
                            "saveState": 118290,
                            "restoreState": 118290,
                            "isEOF": 0,
                            "invalidates": 123817,
                            "keyPattern": {
                                "priority": -1,
                                "used_times": 1,
                                "utime": 1
                            },
                            "indexName": "priority_-1_used_times_1_utime_1",
                            "isMultiKey": false,
                            "direction": "forward",
                            "indexBounds": {
                                "priority": [
                                    "[MaxKey, MinKey]"
                                ],
                                "used_times": [
                                    "[MinKey, MaxKey]"
                                ],
                                "utime": [
                                    "[MinKey, MaxKey]"
                                ]
                            },
                            "keysExamined": 3523496,
                            "dupsTested": 0,
                            "dupsDropped": 0,
                            "seenInvalidated": 0,
                            "matchTested": 0
                        }
                    }
                }
            }
        ]
    },
    "serverInfo": {
        "host": "10-10-231-105",
        "port": 27017,
        "version": "3.0.1",
        "gitVersion": "534b5a3f9d10f00cd27737fbcd951032248b5952"
    }
};


db.Task.find({}).sort({}).limit(50).explain("executionStats");

db.Task.find({"task_name": "images_hotel_hotels_20170929a", "finished": 1}, {_id: 1}).count({applySkipLimit: true});


var query_result = {
    "_id": ObjectId("59d1da65e28b541049823b58"),
    "task_token": "9062ce6e08cc0dbd21fef46e7487da04",
    "args": {
        "url": "https://travelads.hlserve.com/TravelAdsService/v3/Hotels/TravelAdClickRedirect?trackingData=Cmp-qkAgxmJOYm3EzMgli6W1uYDrDONSGmmuhJ+JJIAZphECvanJ9QdBNDRq2bBTxmzpCQgZ61vjdI97TvOFxzcEevo3KjcfCEdJzwaAxHOdfQ2ibtCnTNRfS3CI9SctR1hLX6515APgwK+1pxmwEStGPZMCqHRsgOvXpeSQss1jeJMoBOwd5yr9F/lYrUeW3p+bYahEaLARDiijVSUc6qUBfkRfAz5R8ky1r+TQCyh0Q4uDylvrDIqwD5BAtzlBH8fQZZ+9s1fONTUO1OdfIs5Z3Te2T8078mE5IpMazirh7WCpNez2P2UXHBVeTOIExxT+NsSwC/9Y0RcJXtnv+oS6RgAYO1tH70da+iFHtQYQ6tZ6OPaGR84S6TEtXg8q2vNn3P+NUj2umpZL1JcAGHLeIaGUQ22EmwJWlXjdA2L7paS4a2CyeRZkvXrfF1kZCZs82BGpucg37z9l2aycyk+LOdqgoKzg+AFrfXJMunTU8/720Jp6j/m5TkEMpNulEmrhl2Epv4kp6AarikadjbvofIbKVHg2HqfFPnO4+8Pra2d2yrMdHb9ZNky8mh/iYtWVCI97WSS+RBLr/wa8S80NLwHjdUbe1pLpc5/kCeaZCcalcO9Z5Sh9GdvcWjCyvezxIr0YMyaIF5EqHUnRxPctqa4o+OjVhSCyfL4XpauIc562JzbZI5IS00h1IFCMN1KlOjMi4599/cJp65M9hdnMSOm0nCzL+fIVd2lB467ykPG19+sU25coUX4WvDP75pgiMFxzkLy6MfL+9W0wWFU8OBXysHZyMHZavJA5jsa0ICRMwU0kQTUKNBnPH9b8QNbQOuaSalhc1bvENaiQpn0pwuwRy5LocusjzJVGS3bzjBBw+WgNDTPGkbqaLClbw5UkIvagbvhQJWQ1v3cT2A8DTf5x7d5KtSRZvjdVsLQcUfRU6jkLUdORKmVwxDR1lZCUjg0dqm2mcxqn+l5Wc0x7ie8xNFLXCubsEOeMNYmzdnSLtIgt+OkiGN5nD7ulLFKFfAXdYvTVNK2m09v66IdnoD5fH6SMkg5BoCfB/jhyXZnYpSmooY8E7TFHzRJS+30quP+S6HmHoEMhghpLeUuVgmu138baTTWuONXFwlMj5cM=&rank=3&testVersionOverride=11141.44405.1%2C13487.51625.0%2C14567.99990.0&destinationUrl=https%3A%2F%2Fwww.expedia.com.hk%2FHotels-Hilton-Los-Angeles-Airport.h5907.Hotel-Information&candidateHmGuid=68f748cb-cd7c-47ac-a90c-7dbed2aeed15&beaconIssued=2017-10-02T06:12:45",
        "source": "expedia",
        "part": "detail_hotel_expedia_20170929a",
        "other_info": {"source_id": "5907", "city_id": "NULL"},
        "country_id": "NULL"
    },
    "worker": "proj.hotel_tasks.hotel_base_data",
    "routing_key": "hotel_detail",
    "finished": 0,
    "utime": ISODate("2017-10-19T07:10:00.073Z"),
    "priority": 3,
    "running": 1,
    "used_times": 4,
    "queue": "hotel_detail",
    "task_name": "detail_hotel_expedia_20170929a"
};


var query = db.Task.find({
    $query: {
        "queue": "hotel_detail",
        "priority": 3,
        "finished": 0,
        "running": 0,
        "used_times": 2
    }, $hint: {
        "queue": 1,
        "priority": 1,
        "finished": 1,
        "running": 1,
        "used_times": 1
    }, $explain: 1
}).limit(100);

var query = db.Task.find({
    $query: {
        "queue": "hotel_detail",
        "priority": 3,
        "finished": 0,
        "running": 0,
        "used_times": 6
    }, $hint: {"queue": 1, "finished": 1, "used_times": 1, "priority": 1, "running": 1}
}).limit(100);


var query_plan = {
    "queryPlanner": {
        "plannerVersion": 1,
        "namespace": "MongoTask.Task",
        "indexFilterSet": false,
        "parsedQuery": {"$and": [{"finished": {"$eq": 0}}, {"priority": {"$eq": 3}}, {"queue": {"$eq": "hotel_detail"}}, {"running": {"$eq": 0}}, {"used_times": {"$eq": 2}}]},
        "winningPlan": {
            "stage": "KEEP_MUTATIONS",
            "inputStage": {
                "stage": "FETCH",
                "filter": {"priority": {"$eq": 3}},
                "inputStage": {
                    "stage": "IXSCAN",
                    "keyPattern": {"queue": 1, "finished": 1, "running": 1, "used_times": 1},
                    "indexName": "queue_1_finished_1_running_1_used_times_1",
                    "isMultiKey": false,
                    "direction": "forward",
                    "indexBounds": {
                        "queue": ["[\"hotel_detail\", \"hotel_detail\"]"],
                        "finished": ["[0.0, 0.0]"],
                        "running": ["[0.0, 0.0]"],
                        "used_times": ["[2.0, 2.0]"]
                    }
                }
            }
        },
        "rejectedPlans": [{
            "stage": "KEEP_MUTATIONS",
            "inputStage": {
                "stage": "FETCH",
                "filter": {"$and": [{"finished": {"$eq": 0}}, {"priority": {"$eq": 3}}, {"queue": {"$eq": "hotel_detail"}}, {"used_times": {"$eq": 2}}]},
                "inputStage": {
                    "stage": "IXSCAN",
                    "keyPattern": {"running": 1, "utime": -1},
                    "indexName": "running_1_utime_-1",
                    "isMultiKey": false,
                    "direction": "forward",
                    "indexBounds": {"running": ["[0.0, 0.0]"], "utime": ["[MaxKey, MinKey]"]}
                }
            }
        }, {
            "stage": "KEEP_MUTATIONS",
            "inputStage": {
                "stage": "FETCH",
                "filter": {"$and": [{"finished": {"$eq": 0}}, {"priority": {"$eq": 3}}, {"queue": {"$eq": "hotel_detail"}}, {"used_times": {"$eq": 2}}]},
                "inputStage": {
                    "stage": "IXSCAN",
                    "keyPattern": {"running": 1, "utime": 1},
                    "indexName": "running_1_utime_1",
                    "isMultiKey": false,
                    "direction": "forward",
                    "indexBounds": {"running": ["[0.0, 0.0]"], "utime": ["[MinKey, MaxKey]"]}
                }
            }
        }, {
            "stage": "FETCH",
            "inputStage": {
                "stage": "IXSCAN",
                "keyPattern": {"queue": 1, "finished": 1, "used_times": 1, "priority": 1, "running": 1},
                "indexName": "queue_1_finished_1_used_times_1_priority_1_running_1",
                "isMultiKey": false,
                "direction": "forward",
                "indexBounds": {
                    "queue": ["[\"hotel_detail\", \"hotel_detail\"]"],
                    "finished": ["[0.0, 0.0]"],
                    "used_times": ["[2.0, 2.0]"],
                    "priority": ["[3.0, 3.0]"],
                    "running": ["[0.0, 0.0]"]
                }
            }
        }, {
            "stage": "KEEP_MUTATIONS",
            "inputStage": {
                "stage": "FETCH",
                "filter": {"$and": [{"priority": {"$eq": 3}}, {"used_times": {"$eq": 2}}]},
                "inputStage": {
                    "stage": "IXSCAN",
                    "keyPattern": {"queue": 1, "finished": 1, "running": 1},
                    "indexName": "queue_1_finished_1_running_1",
                    "isMultiKey": false,
                    "direction": "forward",
                    "indexBounds": {
                        "queue": ["[\"hotel_detail\", \"hotel_detail\"]"],
                        "finished": ["[0.0, 0.0]"],
                        "running": ["[0.0, 0.0]"]
                    }
                }
            }
        }, {
            "stage": "KEEP_MUTATIONS",
            "inputStage": {
                "stage": "FETCH",
                "filter": {"$and": [{"finished": {"$eq": 0}}, {"queue": {"$eq": "hotel_detail"}}, {"running": {"$eq": 0}}]},
                "inputStage": {
                    "stage": "IXSCAN",
                    "keyPattern": {"priority": -1, "used_times": 1, "utime": 1},
                    "indexName": "priority_-1_used_times_1_utime_1",
                    "isMultiKey": false,
                    "direction": "forward",
                    "indexBounds": {
                        "priority": ["[3.0, 3.0]"],
                        "used_times": ["[2.0, 2.0]"],
                        "utime": ["[MinKey, MaxKey]"]
                    }
                }
            }
        }]
    },
    "executionStats": {
        "executionSuccess": true,
        "nReturned": 144,
        "executionTimeMillis": 485,
        "totalKeysExamined": 144,
        "totalDocsExamined": 144,
        "executionStages": {
            "stage": "KEEP_MUTATIONS",
            "nReturned": 144,
            "executionTimeMillisEstimate": 0,
            "works": 148,
            "advanced": 144,
            "needTime": 0,
            "needFetch": 3,
            "saveState": 26,
            "restoreState": 26,
            "isEOF": 1,
            "invalidates": 51,
            "inputStage": {
                "stage": "FETCH",
                "filter": {"priority": {"$eq": 3}},
                "nReturned": 144,
                "executionTimeMillisEstimate": 0,
                "works": 148,
                "advanced": 144,
                "needTime": 0,
                "needFetch": 3,
                "saveState": 26,
                "restoreState": 26,
                "isEOF": 1,
                "invalidates": 51,
                "docsExamined": 144,
                "alreadyHasObj": 0,
                "inputStage": {
                    "stage": "IXSCAN",
                    "nReturned": 144,
                    "executionTimeMillisEstimate": 0,
                    "works": 145,
                    "advanced": 144,
                    "needTime": 0,
                    "needFetch": 0,
                    "saveState": 26,
                    "restoreState": 26,
                    "isEOF": 1,
                    "invalidates": 51,
                    "keyPattern": {"queue": 1, "finished": 1, "running": 1, "used_times": 1},
                    "indexName": "queue_1_finished_1_running_1_used_times_1",
                    "isMultiKey": false,
                    "direction": "forward",
                    "indexBounds": {
                        "queue": ["[\"hotel_detail\", \"hotel_detail\"]"],
                        "finished": ["[0.0, 0.0]"],
                        "running": ["[0.0, 0.0]"],
                        "used_times": ["[2.0, 2.0]"]
                    },
                    "keysExamined": 144,
                    "dupsTested": 0,
                    "dupsDropped": 0,
                    "seenInvalidated": 0,
                    "matchTested": 0
                }
            }
        },
        "allPlansExecution": [{
            "nReturned": 0,
            "executionTimeMillisEstimate": 0,
            "totalKeysExamined": 103,
            "totalDocsExamined": 103,
            "executionStages": {
                "stage": "KEEP_MUTATIONS",
                "nReturned": 0,
                "executionTimeMillisEstimate": 0,
                "works": 103,
                "advanced": 0,
                "needTime": 103,
                "needFetch": 0,
                "saveState": 26,
                "restoreState": 26,
                "isEOF": 0,
                "invalidates": 50,
                "inputStage": {
                    "stage": "FETCH",
                    "filter": {"$and": [{"finished": {"$eq": 0}}, {"priority": {"$eq": 3}}, {"queue": {"$eq": "hotel_detail"}}, {"used_times": {"$eq": 2}}]},
                    "nReturned": 0,
                    "executionTimeMillisEstimate": 0,
                    "works": 103,
                    "advanced": 0,
                    "needTime": 103,
                    "needFetch": 0,
                    "saveState": 26,
                    "restoreState": 26,
                    "isEOF": 0,
                    "invalidates": 50,
                    "docsExamined": 103,
                    "alreadyHasObj": 0,
                    "inputStage": {
                        "stage": "IXSCAN",
                        "nReturned": 103,
                        "executionTimeMillisEstimate": 0,
                        "works": 103,
                        "advanced": 103,
                        "needTime": 0,
                        "needFetch": 0,
                        "saveState": 26,
                        "restoreState": 26,
                        "isEOF": 0,
                        "invalidates": 50,
                        "keyPattern": {"running": 1, "utime": -1},
                        "indexName": "running_1_utime_-1",
                        "isMultiKey": false,
                        "direction": "forward",
                        "indexBounds": {"running": ["[0.0, 0.0]"], "utime": ["[MaxKey, MinKey]"]},
                        "keysExamined": 103,
                        "dupsTested": 0,
                        "dupsDropped": 0,
                        "seenInvalidated": 0,
                        "matchTested": 0
                    }
                }
            }
        }, {
            "nReturned": 0,
            "executionTimeMillisEstimate": 0,
            "totalKeysExamined": 103,
            "totalDocsExamined": 103,
            "executionStages": {
                "stage": "KEEP_MUTATIONS",
                "nReturned": 0,
                "executionTimeMillisEstimate": 0,
                "works": 103,
                "advanced": 0,
                "needTime": 103,
                "needFetch": 0,
                "saveState": 26,
                "restoreState": 26,
                "isEOF": 0,
                "invalidates": 50,
                "inputStage": {
                    "stage": "FETCH",
                    "filter": {"$and": [{"finished": {"$eq": 0}}, {"priority": {"$eq": 3}}, {"queue": {"$eq": "hotel_detail"}}, {"used_times": {"$eq": 2}}]},
                    "nReturned": 0,
                    "executionTimeMillisEstimate": 0,
                    "works": 103,
                    "advanced": 0,
                    "needTime": 103,
                    "needFetch": 0,
                    "saveState": 26,
                    "restoreState": 26,
                    "isEOF": 0,
                    "invalidates": 50,
                    "docsExamined": 103,
                    "alreadyHasObj": 0,
                    "inputStage": {
                        "stage": "IXSCAN",
                        "nReturned": 103,
                        "executionTimeMillisEstimate": 0,
                        "works": 103,
                        "advanced": 103,
                        "needTime": 0,
                        "needFetch": 0,
                        "saveState": 26,
                        "restoreState": 26,
                        "isEOF": 0,
                        "invalidates": 50,
                        "keyPattern": {"running": 1, "utime": 1},
                        "indexName": "running_1_utime_1",
                        "isMultiKey": false,
                        "direction": "forward",
                        "indexBounds": {"running": ["[0.0, 0.0]"], "utime": ["[MinKey, MaxKey]"]},
                        "keysExamined": 103,
                        "dupsTested": 0,
                        "dupsDropped": 0,
                        "seenInvalidated": 0,
                        "matchTested": 0
                    }
                }
            }
        }, {
            "nReturned": 99,
            "executionTimeMillisEstimate": 0,
            "totalKeysExamined": 99,
            "totalDocsExamined": 99,
            "executionStages": {
                "stage": "FETCH",
                "nReturned": 99,
                "executionTimeMillisEstimate": 0,
                "works": 103,
                "advanced": 99,
                "needTime": 0,
                "needFetch": 4,
                "saveState": 26,
                "restoreState": 26,
                "isEOF": 0,
                "invalidates": 50,
                "docsExamined": 99,
                "alreadyHasObj": 0,
                "inputStage": {
                    "stage": "IXSCAN",
                    "nReturned": 99,
                    "executionTimeMillisEstimate": 0,
                    "works": 99,
                    "advanced": 99,
                    "needTime": 0,
                    "needFetch": 0,
                    "saveState": 26,
                    "restoreState": 26,
                    "isEOF": 0,
                    "invalidates": 50,
                    "keyPattern": {"queue": 1, "finished": 1, "used_times": 1, "priority": 1, "running": 1},
                    "indexName": "queue_1_finished_1_used_times_1_priority_1_running_1",
                    "isMultiKey": false,
                    "direction": "forward",
                    "indexBounds": {
                        "queue": ["[\"hotel_detail\", \"hotel_detail\"]"],
                        "finished": ["[0.0, 0.0]"],
                        "used_times": ["[2.0, 2.0]"],
                        "priority": ["[3.0, 3.0]"],
                        "running": ["[0.0, 0.0]"]
                    },
                    "keysExamined": 99,
                    "dupsTested": 0,
                    "dupsDropped": 0,
                    "seenInvalidated": 0,
                    "matchTested": 0
                }
            }
        }, {
            "nReturned": 4,
            "executionTimeMillisEstimate": 0,
            "totalKeysExamined": 92,
            "totalDocsExamined": 92,
            "executionStages": {
                "stage": "KEEP_MUTATIONS",
                "nReturned": 4,
                "executionTimeMillisEstimate": 0,
                "works": 103,
                "advanced": 4,
                "needTime": 88,
                "needFetch": 11,
                "saveState": 26,
                "restoreState": 26,
                "isEOF": 0,
                "invalidates": 50,
                "inputStage": {
                    "stage": "FETCH",
                    "filter": {"$and": [{"priority": {"$eq": 3}}, {"used_times": {"$eq": 2}}]},
                    "nReturned": 4,
                    "executionTimeMillisEstimate": 0,
                    "works": 103,
                    "advanced": 4,
                    "needTime": 88,
                    "needFetch": 11,
                    "saveState": 26,
                    "restoreState": 26,
                    "isEOF": 0,
                    "invalidates": 50,
                    "docsExamined": 92,
                    "alreadyHasObj": 0,
                    "inputStage": {
                        "stage": "IXSCAN",
                        "nReturned": 92,
                        "executionTimeMillisEstimate": 0,
                        "works": 92,
                        "advanced": 92,
                        "needTime": 0,
                        "needFetch": 0,
                        "saveState": 26,
                        "restoreState": 26,
                        "isEOF": 0,
                        "invalidates": 50,
                        "keyPattern": {"queue": 1, "finished": 1, "running": 1},
                        "indexName": "queue_1_finished_1_running_1",
                        "isMultiKey": false,
                        "direction": "forward",
                        "indexBounds": {
                            "queue": ["[\"hotel_detail\", \"hotel_detail\"]"],
                            "finished": ["[0.0, 0.0]"],
                            "running": ["[0.0, 0.0]"]
                        },
                        "keysExamined": 92,
                        "dupsTested": 0,
                        "dupsDropped": 0,
                        "seenInvalidated": 0,
                        "matchTested": 0
                    }
                }
            }
        }, {
            "nReturned": 0,
            "executionTimeMillisEstimate": 0,
            "totalKeysExamined": 96,

            "totalDocsExamined": 96,
            "executionStages": {
                "stage": "KEEP_MUTATIONS",
                "nReturned": 0,
                "executionTimeMillisEstimate": 0,
                "works": 103,
                "advanced": 0,
                "needTime": 96,
                "needFetch": 7,
                "saveState": 26,
                "restoreState": 26,
                "isEOF": 0,
                "invalidates": 50,
                "inputStage": {
                    "stage": "FETCH",
                    "filter": {"$and": [{"finished": {"$eq": 0}}, {"queue": {"$eq": "hotel_detail"}}, {"running": {"$eq": 0}}]},
                    "nReturned": 0,
                    "executionTimeMillisEstimate": 0,
                    "works": 103,
                    "advanced": 0,
                    "needTime": 96,
                    "needFetch": 7,
                    "saveState": 26,
                    "restoreState": 26,
                    "isEOF": 0,
                    "invalidates": 50,
                    "docsExamined": 96,
                    "alreadyHasObj": 0,
                    "inputStage": {
                        "stage": "IXSCAN",
                        "nReturned": 96,
                        "executionTimeMillisEstimate": 0,
                        "works": 96,
                        "advanced": 96,
                        "needTime": 0,
                        "needFetch": 0,
                        "saveState": 26,
                        "restoreState": 26,
                        "isEOF": 0,
                        "invalidates": 50,
                        "keyPattern": {"priority": -1, "used_times": 1, "utime": 1},
                        "indexName": "priority_-1_used_times_1_utime_1",
                        "isMultiKey": false,
                        "direction": "forward",
                        "indexBounds": {
                            "priority": ["[3.0, 3.0]"],
                            "used_times": ["[2.0, 2.0]"],
                            "utime": ["[MinKey, MaxKey]"]
                        },
                        "keysExamined": 96,
                        "dupsTested": 0,
                        "dupsDropped": 0,
                        "seenInvalidated": 0,
                        "matchTested": 0
                    }
                }
            }
        }, {
            "nReturned": 100,
            "executionTimeMillisEstimate": 0,
            "totalKeysExamined": 100,
            "totalDocsExamined": 100,
            "executionStages": {
                "stage": "KEEP_MUTATIONS",
                "nReturned": 100,
                "executionTimeMillisEstimate": 0,
                "works": 103,
                "advanced": 100,
                "needTime": 0,
                "needFetch": 3,
                "saveState": 25,
                "restoreState": 25,
                "isEOF": 0,
                "invalidates": 50,
                "inputStage": {
                    "stage": "FETCH",
                    "filter": {"priority": {"$eq": 3}},
                    "nReturned": 100,
                    "executionTimeMillisEstimate": 0,
                    "works": 103,
                    "advanced": 100,
                    "needTime": 0,
                    "needFetch": 3,
                    "saveState": 25,
                    "restoreState": 25,
                    "isEOF": 0,
                    "invalidates": 50,
                    "docsExamined": 100,
                    "alreadyHasObj": 0,
                    "inputStage": {
                        "stage": "IXSCAN",
                        "nReturned": 100,
                        "executionTimeMillisEstimate": 0,
                        "works": 100,
                        "advanced": 100,
                        "needTime": 0,
                        "needFetch": 0,
                        "saveState": 25,
                        "restoreState": 25,
                        "isEOF": 0,
                        "invalidates": 50,
                        "keyPattern": {"queue": 1, "finished": 1, "running": 1, "used_times": 1},
                        "indexName": "queue_1_finished_1_running_1_used_times_1",
                        "isMultiKey": false,
                        "direction": "forward",
                        "indexBounds": {
                            "queue": ["[\"hotel_detail\", \"hotel_detail\"]"],
                            "finished": ["[0.0, 0.0]"],
                            "running": ["[0.0, 0.0]"],
                            "used_times": ["[2.0, 2.0]"]
                        },
                        "keysExamined": 100,
                        "dupsTested": 0,
                        "dupsDropped": 0,
                        "seenInvalidated": 0,
                        "matchTested": 0
                    }
                }
            }
        }]
    },
    "serverInfo": {
        "host": "10-10-231-105",
        "port": 27017,
        "version": "3.0.1",
        "gitVersion": "534b5a3f9d10f00cd27737fbcd951032248b5952"
    }
};

var query = db.Task.find({
    $query: {"task_name": "detail_hotel_agoda_20170929a"},
    $hint: {"task_name": 1},
    $explain: 1
}).limit(100);

var count_quer = db.Task.find({
    $query: {"task_name": "list_hotel_ctrip_20170929a"},
    $hint: {"task_name": 1},
    $explain: 1
}).count();

db.Task.find({
    $query: {"task_name": "images_hotel_ctrip_20170929a", "finished": 0},
    $hint: {"task_name": 1, "finished": 1}
});

db.Task.find({
    $query: {
        'running': 1, 'utime': {
            '$lt': new Date(ISODate().getTime() - 1000 * 60 * 60)
        }
    },
    $hint: {'running': 1, 'utime': -1}
}).limit(5000).update({
    $set: {
        'finished': 0,
        'used_times': 0,
        'running': 0
    }
}, false, true);

db.Task.find({
        'running': 1, 'utime': {
            '$lt': new Date(ISODate().getTime() - 1000 * 60 * 60)
        }
    }
).hint({'running': 1, 'utime': -1}).limit(5000).update({
    $set: {
        'finished': 0,
        'used_times': 0,
        'running': 0
    }
}, false, true);


db.Task.find({
        'running': 1, 'utime': {
            '$lt': new Date(ISODate().getTime() - 1000 * 60 * 60)
        }
    }
).update({
    $set: {
        'finished': 0,
        'used_times': 0,
        'running': 0
    }
}, false, true);

db.Task.count({
    $query: {"task_name": "detail_hotel_agoda_20170929a"},
    $hint: {"task_name": 1}
});

db.Task.find({"task_name": "list_hotel_agoda_20170928d", "finished": 0}).hint({"task_name": 1, "finished": 1}).count();


db.Task.find({'running': 1, 'utime': {'$lt': new Date(new Date().getTime() - 60 * 60 * 1000)}}).hint({
    "running": 1,
    "utime": -1
}).count();

db.Task.update({task_name: "image_wanle_huantaoyou_20171023a"}, {
    $set: {
        'finished': 0,
        'used_times': 0,
        'running': 0
    }
}, false, true);
{
    task_name:"image_wanle_huantaoyou_20171023a"
}

db.Task.find({"task_name": "detail_hotel_agoda_20170929a"}).hint({"task_name": 1}).count();

var iter_counter = db.Task.find({
    $query: {"task_name": "detail_hotel_agoda_20170929a"},
    $hint: {"task_name": 1},
    $explain: 1
}).itcount();

query_plan = {
    "queryPlanner": {
        "plannerVersion": 1,
        "namespace": "test.Task",
        "indexFilterSet": false,
        "parsedQuery": {"task_name": {"$eq": "detail_hotel_agoda_20170929a"}},
        "winningPlan": {"stage": "EOF"},
        "rejectedPlans": []
    },
    "executionStats": {
        "executionSuccess": true,
        "nReturned": 0,
        "executionTimeMillis": 0,
        "totalKeysExamined": 0,
        "totalDocsExamined": 0,
        "executionStages": {
            "stage": "EOF",
            "nReturned": 0,
            "executionTimeMillisEstimate": 0,
            "works": 1,
            "advanced": 0,
            "needTime": 0,
            "needFetch": 0,
            "saveState": 0,
            "restoreState": 0,
            "isEOF": 1,
            "invalidates": 0
        },
        "allPlansExecution": []
    },
    "serverInfo": {
        "host": "10-10-231-105",
        "port": 27017,
        "version": "3.0.1",
        "gitVersion": "534b5a3f9d10f00cd27737fbcd951032248b5952"
    }
};


db.detail_final_data.aggregate(
    [
        {
            "$match": {
                "loc":
                    {
                        "$geoWithin": {
                            "$centerSphere": [[2.351492339147967, 48.85746107178952],
                                50 / 6378.1]
                        }
                    }
            }
        },
        {
            "$group": {
                "_id": {"source": "$source", "source_city_id": "$source_city_id"},
                "count": {"$sum": 1}
            }
        }
    ]
);

// renew
var indexes = db.TaskBak1102.getIndexes();

indexes.forEach(function (index) {
    delete index.v;
    delete index.ns;

    var options = [];
    for (var option in index) {
        if (option !== 'key') {
            options.push(index['option']);
        }
    }
    db.Task.createIndex(index.key, options);
});

db.Task.createIndex(key, options);


db.Task.find({"finished": 1}).hint({"finished": 1}).count();

db.Task.createIndex({finished: 1});
db.Task.createIndex({task_token: 1}, unique = true);


db.Task.update({task_name: "merge_hotel_image_20171107"}, {
    $set: {

        'finished': 0,
        'used_times': 0,
        'running': 0
    }
}, false, true);

db.Task.remove({task_name: "merge_hotel_image_20171108_40"});


var per_task = {
    "_id": ObjectId("59ce57cfe28b54390cb8146a"),
    "task_token": "f6c806aa73728ad62049ba1613d7ed6c",
    "args": {
        "suggest_type": 2,
        "check_in": "20171228",
        "city_id": "10002",
        "suggest": "{\"label_highlighted\": \"\\u7f57\\u9a6c, \\u62c9\\u9f50\\u5965\\u5927\\u533a, \\u610f\\u5927\\u5229\", \"label_cjk\": \"<span class='search_hl_cjk'>\\u7f57\\u9a6c</span> <span class='search_hl_cjk'>\\u62c9\\u9f50\\u5965\\u5927\\u533a</span>, <span class='search_hl_cjk'>\\u610f\\u5927\\u5229</span>\", \"__part\": 0, \"lc\": \"zh\", \"genius_hotels\": \"2508\", \"rtl\": 0, \"hotels\": \"9749\", \"dest_id\": \"-126693\", \"cc1\": \"it\", \"label_multiline\": \"<span>\\u7f57\\u9a6c</span> \\u62c9\\u9f50\\u5965\\u5927\\u533a, \\u610f\\u5927\\u5229\", \"nr_hotels_25\": \"10335\", \"_ef\": [{\"name\": \"ac_popular_badge\", \"value\": 1}], \"labels\": [{\"text\": \"\\u7f57\\u9a6c\", \"required\": 1, \"type\": \"city\", \"hl\": 1}, {\"text\": \"\\u62c9\\u9f50\\u5965\\u5927\\u533a\", \"required\": 1, \"type\": \"region\", \"hl\": 1}, {\"text\": \"\\u610f\\u5927\\u5229\", \"required\": 1, \"type\": \"country\", \"hl\": 1}], \"__query_covered\": 9, \"flags\": {\"popular\": 1}, \"nr_hotels\": \"9749\", \"city_ufi\": null, \"label\": \"\\u7f57\\u9a6c, \\u62c9\\u9f50\\u5965\\u5927\\u533a, \\u610f\\u5927\\u5229\", \"type\": \"ci\", \"dest_type\": \"city\", \"region_id\": \"902\"}",
        "country_id": "205",
        "source": "booking",
        "part": "20170929a",
        "is_new_type": 1
    },
    "worker": "proj.hotel_list_task.hotel_list_task",
    "routing_key": "hotel_list",
    "finished": 1,
    "utime": ISODate("2017-10-08T07:13:40.091Z"),
    "priority": 3,
    "list_task_token": "dbb1f99c5f49932288bd0fefec1c4927",
    "running": 0,
    "used_times": 1,
    "queue": "hotel_list",
    "task_name": "list_hotel_booking_20170929a",
    "insert_data": "",
};


db.City_Queue_poi_list_TaskName_city_total_qyer_20171120a.update({}, {$set: {finished: 0}}, false, true);

db.City_Queue_poi_list_TaskName_city_total_daodao_20171120a.update({}, {$set: {finished: 0}}, false, true);

db.City_Queue_poi_list_TaskName_city_total_qyer_20171120a.update({}, {$set: {date_index: 0}}, false, true);

db.Task_Queue_poi_list_TaskName_list_total_qyer_20171120a.update({task_name: "list_total_qyer_20171120a"}, {
    $set: {

        'finished': 0,
        'used_times': 0,
        'running': 0
    }
}, false, true);

db.Task_Queue_file_downloader_TaskName_google_drive_task_20171121.update({}, {
    $set: {

        'finished': 0,
        'used_times': 0,
        'running': 0
    }
}, false, true);

db.City_Queue_poi_list_TaskName_city_total_qyer_20171120a.update({}, {
    $set: {
        'finished': 0,
        'data_count': [],
        'task_result': [],
        'date_index': 0
    }
}, false, true);

db.Task_Queue_poi_list_TaskName_list_total_qyer_20171120a.update({'finished': 0}, {
    $set: {
        'running': 0,
        'used_times': 0
    }
}, false, true);


db.Task_Queue_poi_list_TaskName_list_total_qyer_20171120a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);


db.Task_Queue_hotel_list_TaskName_list_hotel_hotels_20171122a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);

db.City_Queue_hotel_list_TaskName_city_hotel_hotels_20171122a.update({}, {
    $set: {
        'finished': 0,
        'data_count': [],
        'task_result': [],
        'date_index': 0
    }
}, false, true);


db.Task_Queue_hotel_list_TaskName_list_hotel_booking_20171122a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);

db.City_Queue_hotel_list_TaskName_city_hotel_booking_20171122a.update({}, {
    $set: {
        'finished': 0,
        'data_count': [],
        'task_result': [],
        'date_index': 0
    }
}, false, true);


db.Task_Queue_hotel_list_TaskName_list_hotel_ctrip_20171122a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);
db.City_Queue_hotel_list_TaskName_city_hotel_ctrip_20171122a.update({}, {
    $set: {
        'finished': 0,
        'data_count': [],
        'task_result': [],
        'date_index': 0
    }
}, false, true);


db.Task_Queue_hotel_list_TaskName_list_hotel_expedia_20171122a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);
db.City_Queue_hotel_list_TaskName_city_hotel_expedia_20171122a.update({}, {
    $set: {
        'finished': 0,
        'data_count': [],
        'task_result': [],
        'date_index': 0
    }
}, false, true);


db.Task_Queue_hotel_list_TaskName_list_hotel_elong_20171122a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);
db.City_Queue_hotel_list_TaskName_city_hotel_elong_20171122a.update({}, {
    $set: {
        'finished': 0,
        'data_count': [],
        'task_result': [],
        'date_index': 0
    }
}, false, true);


db.Task_Queue_hotel_list_TaskName_list_hotel_agoda_20171122a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);
db.City_Queue_hotel_list_TaskName_city_hotel_agoda_20171122a.update({}, {
    $set: {
        'finished': 0,
        'data_count': [],
        'task_result': [],
        'date_index': 0
    }
}, false, true);


db.Task_Queue_poi_list_TaskName_list_total_qyer_20171120a.update({"list_task_token": "8d29d81b940c52bca6f42638fc46a72f"}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);

db.Task_Queue_file_downloader_TaskName_images_hotel_booking_20171122a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);
db.Task_Queue_file_downloader_TaskName_images_hotel_agoda_20171122a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);
db.Task_Queue_file_downloader_TaskName_images_hotel_ctrip_20171122a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);
db.Task_Queue_file_downloader_TaskName_images_hotel_hotels_20171122a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);
db.Task_Queue_file_downloader_TaskName_images_hotel_expedia_20171122a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);

db.Task_Queue_file_downloader_TaskName_images_attr_daodao_20171122a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);

db.Task_Queue_hotel_detail_TaskName_detail_hotel_agoda_20171122a.remove({});
db.Task_Queue_hotel_detail_TaskName_detail_hotel_booking_20171122a.remove({});
db.Task_Queue_hotel_detail_TaskName_detail_hotel_ctrip_20171122a.remove({});
db.Task_Queue_hotel_detail_TaskName_detail_hotel_hotels_20171122a.remove({});
db.Task_Queue_hotel_detail_TaskName_detail_hotel_expedia_20171122a.remove({});
db.Task_Queue_hotel_detail_TaskName_detail_hotel_elong_20171122a.remove({});


db.Task_Queue_hotel_detail_TaskName_detail_hotel_elong_20171127a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);

db.Task_Queue_hotel_detail_TaskName_detail_hotel_expedia_20171127a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);

db.Task_Queue_hotel_detail_TaskName_detail_hotel_booking_20171127a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);

db.Task_Queue_poi_detail_TaskName_detail_total_qyer_20171120a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0,
        // 'priority': 4
    }
}, false, true);


db.Task_Queue_hotel_detail_TaskName_detail_hotel_agoda_20171127a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);

db.Task_Queue_poi_list_TaskName_list_total_qyer_20171208a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);


db.Task_Queue_poi_detail_TaskName_detail_total_qyer_20171201a.update({finished: 0}, {
    $set: {
        'running': 0,
        'used_times': 0
    }
}, false, true);

db.Task_Queue_poi_detail_TaskName_detail_total_qyer_20171120a.update({finished: 0}, {
    $set: {
        'running': 0,
        'used_times': 0
    }
}, false, true);


db.Task_Queue_poi_detail_TaskName_detail_total_qyer_20171209a.update({finished: 0}, {
    $set: {
        'running': 0,
        'used_times': 0
    }
}, false, true);

db.Task_Queue_supplement_field_TaskName_baidu_search_20171211a.update({finished: 0}, {
    $set: {
        'running': 0,
        'used_times': 0
    }
}, false, true);

db.Task_Queue_hotel_detail_TaskName_detail_hotel_holiday_20171226a.update({finished: 0}, {
    $set: {
        'running': 0,
        'used_times': 0
    }
}, false, true);


db.Task_Queue_hotel_detail_TaskName_detail_hotel_ihg_20171221a.update({}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);


db.Task_Queue_merge_task_TaskName_merge_hotel_image_20180108_20.update({
    'args.uid': {
        $in: ['ht11703219', 'ht11703210', 'ht11703237', 'ht11703474', 'ht11703426', 'ht10296130', 'ht11191695', 'ht11703443', 'ht10884051', 'ht10317827', 'ht11703502', 'ht10446878', 'ht11703494', 'ht11703369', 'ht11376694', 'ht11308741', 'ht11703342', 'ht11048870', 'ht11587785', 'ht11486881', 'ht11703238', 'ht10817189', 'ht11703451', 'ht11703439', 'ht10993442', 'ht10229144', 'ht10226758', 'ht10565318', 'ht10568151', 'ht10706237', 'ht11065798', 'ht11248962', 'ht11703087', 'ht11703093', 'ht10344775', 'ht11703319', 'ht11703367', 'ht11703360', 'ht11072647', 'ht10834348', 'ht11449393', 'ht10677212', 'ht11045544', 'ht11203305', 'ht11703327', 'ht11205083', 'ht11703333', 'ht11514717', 'ht11703349', 'ht11703357', 'ht11047087', 'ht11514724', 'ht11703348', 'ht11514721', 'ht10359988', 'ht11703328', 'ht11703224', 'ht10712304', 'ht11703298', 'ht11177024', 'ht10709581', 'ht11703364', 'ht11703515', 'ht11703469', 'ht10787119', 'ht11703084', 'ht11703220', 'ht10691137', 'ht11703335', 'ht11703337', 'ht10248089', 'ht10247580', 'ht11029351', 'ht11598455', 'ht11570608', 'ht11703215', 'ht11465413', 'ht11490600', 'ht11451318', 'ht10773828', 'ht10774185', 'ht11703534', 'ht11698790', 'ht11621967', 'ht11264295', 'ht11265979', 'ht11561314', 'ht11561313', 'ht11171178', 'ht11485294', 'ht10505523', 'ht11703300', 'ht11703221', 'ht10530857', 'ht10530852', 'ht10883444', 'ht11523320', 'ht10883550', 'ht11703421', 'ht11703422', 'ht10324051', 'ht11286460', 'ht11703431', 'ht10302992', 'ht10303299', 'ht10303061', 'ht10762572', 'ht10313000', 'ht11514479', 'ht11669094', 'ht11308016', 'ht10721685', 'ht10350717', 'ht11703171', 'ht11703160', 'ht10469582', 'ht11703413', 'ht11703305', 'ht10244623', 'ht11541954', 'ht11703418', 'ht11290171', 'ht10425992', 'ht11703207', 'ht11703529', 'ht10425748', 'ht10823333', 'ht10424495', 'ht10757538', 'ht11299192', 'ht11656618', 'ht11120358', 'ht11114770', 'ht11703046', 'ht10411389', 'ht11703532', 'ht11703066', 'ht11034332', 'ht11703392', 'ht10336652', 'ht11703387', 'ht11034343', 'ht11350745', 'ht11356095', 'ht11227281', 'ht11703296', 'ht10391098', 'ht11703278', 'ht11703297', 'ht11627107', 'ht10680857', 'ht11703099', 'ht11703142', 'ht11703159', 'ht11703152', 'ht11467054', 'ht11494867', 'ht11703070', 'ht11703051', 'ht10380251', 'ht10377796', 'ht10780618', 'ht11703354', 'ht10773961', 'ht11044756', 'ht11703436', 'ht11387989', 'ht10720762', 'ht10829829', 'ht10797920', 'ht11444260', 'ht11126232', 'ht11703157', 'ht11703409', 'ht11703324', 'ht10777661', 'ht11703326', 'ht11501109', 'ht11328814', 'ht10334053', 'ht11304651', 'ht10346796', 'ht10346505', 'ht11703166', 'ht11703193', 'ht11703204', 'ht11703182', 'ht10771608', 'ht10346096', 'ht10772105', 'ht11703161', 'ht11703177', 'ht11703170', 'ht11703200', 'ht11703196', 'ht11703072', 'ht11311751', 'ht11212571', 'ht11703434', 'ht10763763', 'ht11703195', 'ht10789119', 'ht11703064', 'ht10789153', 'ht10756282', 'ht11703146', 'ht11065822', 'ht10353801', 'ht11703067', 'ht11703054', 'ht11703153', 'ht10741788', 'ht11703385', 'ht11703312', 'ht11703416', 'ht10334498', 'ht10333161', 'ht11703465', 'ht11703264', 'ht11171640', 'ht11362889', 'ht11171637', 'ht11703481', 'ht10317053', 'ht11703512', 'ht11703048', 'ht11703358', 'ht11703331', 'ht11703361', 'ht11703279', 'ht10354579', 'ht11385366', 'ht10841376', 'ht10760073', 'ht11422496', 'ht11703118', 'ht10758808', 'ht11703373', 'ht10328118', 'ht10327360', 'ht10328406', 'ht11465202', 'ht10737097', 'ht11703332', 'ht11331723', 'ht11703449', 'ht11703334', 'ht10409179', 'ht10299671', 'ht10299559', 'ht11703168', 'ht11703441', 'ht10339046', 'ht10339495', 'ht10753059', 'ht11371050', 'ht11703507', 'ht11703468', 'ht11028059', 'ht11703125', 'ht11703143', 'ht11703482', 'ht11703521', 'ht11197865', 'ht11703497', 'ht11703145', 'ht11703475', 'ht11703513', 'ht11703261', 'ht10393679', 'ht10783345', 'ht10781057', 'ht10502894', 'ht11098688', 'ht10503889', 'ht11097997', 'ht11703483', 'ht10989944', 'ht10269560', 'ht10271261', 'ht10723561', 'ht11703516', 'ht10319177', 'ht11194169', 'ht10319514', 'ht11703492', 'ht11703488', 'ht11703478', 'ht11288219', 'ht11289776', 'ht11703304', 'ht11703094', 'ht11703514', 'ht11703526', 'ht11396564', 'ht11484882', 'ht10711128', 'ht11703308', 'ht10711133', 'ht10246617', 'ht11205926', 'ht11647144', 'ht11703410', 'ht11703386', 'ht11703405', 'ht11033864', 'ht11703344', 'ht10785788', 'ht11703353', 'ht10366399', 'ht10367862', 'ht11703346', 'ht11703329', 'ht11703090', 'ht10249939', 'ht10249714', 'ht11120839', 'ht11499294', 'ht11703393', 'ht11642386', 'ht10249936', 'ht11455509', 'ht11286392', 'ht11703318', 'ht10819615', 'ht11703187', 'ht10745590', 'ht10336445', 'ht11703351', 'ht11638025', 'ht11521440', 'ht11657970', 'ht10412177', 'ht11413170', 'ht11703322', 'ht11703356', 'ht10332685', 'ht11703225', 'ht10297019', 'ht11703419', 'ht10738924', 'ht10757741', 'ht10413337', 'ht11703194', 'ht10343878', 'ht11212307', 'ht10221445', 'ht11703338', 'ht10262841', 'ht11703302', 'ht11703254', 'ht10412512', 'ht11703247', 'ht10817904', 'ht11049221', 'ht10708954', 'ht11235335', 'ht11703095', 'ht10319017', 'ht11703268', 'ht10299696', 'ht11703306', 'ht10412425', 'ht10541640', 'ht11703464', 'ht10250828', 'ht11703061', 'ht11212935', 'ht11703060', 'ht11703049', 'ht11703065', 'ht11052007', 'ht10375630', 'ht10388304', 'ht10390516', 'ht11703097', 'ht10585852', 'ht11703287', 'ht11703136', 'ht11703121', 'ht11703378', 'ht11703498', 'ht11703508', 'ht11703505', 'ht11703484', 'ht10315250', 'ht11703320', 'ht11703340', 'ht11703376', 'ht11703403', 'ht11703454', 'ht11021602', 'ht11703425', 'ht11703495', 'ht11703102', 'ht11703119', 'ht11703446', 'ht11703459', 'ht11703323', 'ht10325649', 'ht11703140', 'ht11703113', 'ht11703141', 'ht10873379', 'ht11237166', 'ht11703191', 'ht10747863', 'ht11703285', 'ht10354386', 'ht11703345', 'ht11310900', 'ht11050212', 'ht11703079', 'ht11703442', 'ht11703275', 'ht11035280', 'ht10783001', 'ht10778039', 'ht11426087', 'ht11251964', 'ht10907824', 'ht11703424', 'ht10348819', 'ht10771423', 'ht11481694', 'ht11477618', 'ht11703525', 'ht11542216', 'ht10331792', 'ht10761455', 'ht10760552', 'ht11703203', 'ht11703199', 'ht11703292', 'ht10379308', 'ht11337800', 'ht11411128', 'ht10196975', 'ht10993371', 'ht11069550', 'ht10377880', 'ht11703076', 'ht11703295', 'ht10387647', 'ht11698651', 'ht11703271', 'ht11635036', 'ht11703524', 'ht11575519', 'ht11575515', 'ht11045855', 'ht10359764', 'ht10360864', 'ht10793567', 'ht11703396', 'ht11703407', 'ht11703107', 'ht11703098', 'ht11703135', 'ht11703132', 'ht11703096', 'ht10757432', 'ht11303800', 'ht11703109', 'ht11703129', 'ht10323509', 'ht11703114', 'ht11703127', 'ht10324331', 'ht11703103', 'ht11028643', 'ht10324191', 'ht11703116', 'ht11703138', 'ht11703120', 'ht11703117', 'ht11703130', 'ht10323599', 'ht11703150', 'ht10323488', 'ht11703151', 'ht11703147', 'ht11703144', 'ht11703106', 'ht10323797', 'ht10323431', 'ht11703128', 'ht11703110', 'ht11301267', 'ht10817224', 'ht11703256', 'ht10421276', 'ht10315200', 'ht11106689', 'ht10775495', 'ht11703190', 'ht10769005', 'ht11703082', 'ht10362742', 'ht10362826', 'ht10889834', 'ht11703228', 'ht11214792', 'ht11703500', 'ht11703489', 'ht11703467', 'ht11703455', 'ht11703229', 'ht11703209', 'ht11703270', 'ht10774626', 'ht11703180', 'ht11703173', 'ht11703186', 'ht10352403', 'ht11044249', 'ht11703165', 'ht11703158', 'ht11703162', 'ht11703181', 'ht11703176', 'ht10812317', 'ht10211325', 'ht11631941', 'ht11668270', 'ht10213894', 'ht11283265', 'ht10718425', 'ht10769533', 'ht11703370', 'ht11703374', 'ht11698796', 'ht11054384', 'ht10376690', 'ht11703075', 'ht11703391', 'ht11703499', 'ht10996687', 'ht10699758', 'ht10234762', 'ht11703368', 'ht11024511', 'ht10751068', 'ht11703284', 'ht11583378', 'ht11703269', 'ht11703293', 'ht11703240', 'ht10984819', 'ht11169032', 'ht10986279', 'ht10327942', 'ht10344391', 'ht11283277', 'ht11703423', 'ht11703126', 'ht10827653', 'ht11570733', 'ht11611777', 'ht11703086', 'ht11703069', 'ht10369133', 'ht11703476', 'ht10757124', 'ht11703108', 'ht11703134', 'ht10828724', 'ht10972187', 'ht11703527', 'ht10735833', 'ht11703522', 'ht10751501', 'ht10806293', 'ht10709946', 'ht11703314', 'ht11202838', 'ht10374135', 'ht10359281', 'ht11703363', 'ht11703352', 'ht11703450', 'ht11572031', 'ht11703428', 'ht11703427', 'ht11703460', 'ht11703520', 'ht11703447', 'ht11591204', 'ht10727782', 'ht10728048', 'ht10727549', 'ht10280367', 'ht11296082', 'ht11703433', 'ht11591206', 'ht11703440', 'ht10302125', 'ht10302411', 'ht10330516', 'ht10330526', 'ht10215735', 'ht10215166', 'ht11657401', 'ht10990848', 'ht10887182', 'ht10360315', 'ht10780629', 'ht11703235', 'ht11703406', 'ht11703412', 'ht11110840', 'ht10325923', 'ht11568525', 'ht11675289', 'ht10857588', 'ht11637886', 'ht11703379', 'ht11032928', 'ht10333116', 'ht11370479', 'ht11490376', 'ht11703149', 'ht11703148', 'ht11448249', 'ht11703438', 'ht11703184', 'ht10401193', 'ht11357852', 'ht11703133', 'ht10753725', 'ht11703105', 'ht10405217', 'ht11608332', 'ht11634071', 'ht11528167', 'ht11654908', 'ht10890845', 'ht11392413', 'ht11561433', 'ht11334556', 'ht11114175', 'ht10548302', 'ht11698485', 'ht11650033', 'ht11669517', 'ht11623568', 'ht11703531', 'ht10547285', 'ht11501354', 'ht11703432', 'ht10524925', 'ht11329090', 'ht10523660', 'ht11329071', 'ht10743862', 'ht11703435', 'ht11703377', 'ht11167849', 'ht10295907', 'ht11119637', 'ht11011988', 'ht10278506', 'ht10302449', 'ht10739665', 'ht11703453', 'ht11149315', 'ht11105700', 'ht11105714', 'ht11703172', 'ht11523645', 'ht11106964', 'ht11047687', 'ht11703062', 'ht11703058', 'ht11051871', 'ht11703059', 'ht11309113', 'ht11703077', 'ht10877010', 'ht11568474', 'ht11595160', 'ht11703233', 'ht10402985', 'ht11703216', 'ht10404322', 'ht10810292', 'ht11361957', 'ht11453365', 'ht11486078', 'ht11552564', 'ht11607891', 'ht10769194', 'ht10340466', 'ht11202558', 'ht11703408', 'ht11703457', 'ht10307336', 'ht10743281', 'ht10744858', 'ht11021372', 'ht10748448', 'ht11516465', 'ht10262756', 'ht11200924', 'ht11703179', 'ht11703167', 'ht10352261', 'ht10386261', 'ht11703104', 'ht11131838', 'ht10067066', 'ht11259437', 'ht11703185', 'ht10886971', 'ht11703100', 'ht10326127', 'ht10759606', 'ht10327382', 'ht11703111', 'ht11703401', 'ht11703122', 'ht11703366', 'ht11703124', 'ht10761172', 'ht11703383', 'ht11030637', 'ht11703163', 'ht11703189', 'ht10772651', 'ht11703192', 'ht10769833', 'ht10796424', 'ht11703055', 'ht11703123', 'ht10887206', 'ht11180044', 'ht11703283', 'ht11703183', 'ht11542902', 'ht11703437', 'ht11703430', 'ht11621158', 'ht10699718', 'ht11703301', 'ht10743487', 'ht10742129', 'ht10348028', 'ht10381034', 'ht10350727', 'ht10422626', 'ht10422693', 'ht11250508', 'ht10251939', 'ht10719302', 'ht10251665', 'ht10713281', 'ht10250926', 'ht11703272', 'ht10768328', 'ht10342836', 'ht10768500', 'ht11703155', 'ht10984882', 'ht11336182', 'ht10287173', 'ht11698640', 'ht11703384', 'ht11703404', 'ht10338622', 'ht10765551', 'ht11703390', 'ht11703375', 'ht11703315', 'ht10744351', 'ht11023142', 'ht11703485', 'ht11703206', 'ht11703280', 'ht11703250', 'ht11703313', 'ht10483697', 'ht10450652', 'ht11703242', 'ht10230034', 'ht11285903', 'ht11393799', 'ht10884513', 'ht11108289', 'ht11364783', 'ht10270778', 'ht11703389', 'ht10403244', 'ht11063663', 'ht10812244', 'ht11703218', 'ht11079942', 'ht10827471', 'ht11644707', 'ht11703266', 'ht11310785', 'ht11703249', 'ht10798697', 'ht11703415', 'ht11332237', 'ht10225916', 'ht11703274', 'ht10817940', 'ht10412815', 'ht11703230', 'ht11628992', 'ht10344779', 'ht11703445', 'ht10536054', 'ht11703411', 'ht10347942', 'ht11074903', 'ht10411969', 'ht11320715', 'ht11703496', 'ht11703477', 'ht11703518', 'ht11703519', 'ht11703472', 'ht11703490', 'ht11703486', 'ht11703307', 'ht11703528', 'ht11703339', 'ht11703398', 'ht11703112', 'ht10754728', 'ht11703131', 'ht10757238', 'ht10322223', 'ht10282826', 'ht11088509', 'ht11233972', 'ht10347546', 'ht11703236', 'ht10407113', 'ht11703234', 'ht10403819', 'ht11703217', 'ht11703226', 'ht11703222', 'ht11226172', 'ht11703530', 'ht11224283', 'ht11505485', 'ht10323099', 'ht11703309', 'ht10767311', 'ht10388078', 'ht11636933', 'ht11698503', 'ht10902997', 'ht11525737', 'ht11686673', 'ht11703213', 'ht10799065', 'ht11493505', 'ht11703429', 'ht11703053', 'ht11308772', 'ht11431205', 'ht11309216', 'ht11703081', 'ht11703047', 'ht11049728', 'ht11601880', 'ht11703073', 'ht11464496', 'ht11703212', 'ht11703211', 'ht11703239', 'ht11703223', 'ht11703246', 'ht10409000', 'ht11703227', 'ht11296291', 'ht10734031', 'ht11703372', 'ht10341973', 'ht10799580', 'ht11703083', 'ht11703088', 'ht10796253', 'ht10384223', 'ht10798193', 'ht10798782', 'ht10384854', 'ht10385689', 'ht10515863', 'ht10774879', 'ht10815577', 'ht11424155', 'ht10258691', 'ht11703154', 'ht10459074', 'ht10707665', 'ht11703139', 'ht10637118', 'ht11703420', 'ht11597727', 'ht10819102', 'ht11703232', 'ht11018552', 'ht10746752', 'ht11298789', 'ht11207717', 'ht10429295', 'ht11513824', 'ht11511782', 'ht10832831', 'ht10554993', 'ht10102584', 'ht11105838', 'ht10743667', 'ht10741039', 'ht11703359', 'ht10813989', 'ht11703241', 'ht11703258', 'ht11056777', 'ht10390115', 'ht10389345', 'ht11703257', 'ht11703290', 'ht11242831', 'ht11703174', 'ht11703175', 'ht11703388', 'ht11703253', 'ht11703276', 'ht11703252', 'ht11063154', 'ht11703288', 'ht11703294', 'ht10417619', 'ht10620086', 'ht10724005', 'ht11703273', 'ht10111386', 'ht11445728', 'ht10762447', 'ht11703463', 'ht10243835', 'ht10243654', 'ht10707117', 'ht11703259', 'ht11703317', 'ht10413211', 'ht10281736', 'ht11703452', 'ht11703417', 'ht10282709', 'ht11703414', 'ht11230902', 'ht11435744', 'ht11199558', 'ht11372609', 'ht11703517', 'ht11703471', 'ht10308071', 'ht11703491', 'ht11703493', 'ht11703479', 'ht11026789', 'ht11703506', 'ht11703503', 'ht11703504', 'ht11193082', 'ht11703510', 'ht11703470', 'ht11562787', 'ht10311471', 'ht11703466', 'ht11703091', 'ht11703085', 'ht10404941', 'ht11703169', 'ht11703205', 'ht10425666', 'ht10428420', 'ht11703355', 'ht11703321', 'ht11044142', 'ht11703325', 'ht11384963', 'ht10428150', 'ht11180866', 'ht11703311', 'ht10265743', 'ht10007206', 'ht11520838', 'ht11434103', 'ht11331722', 'ht11703299', 'ht11293398', 'ht11703310', 'ht10721565', 'ht10267531', 'ht10265900', 'ht11007683', 'ht11703245', 'ht11698760', 'ht11703394', 'ht10335130', 'ht10400285', 'ht11538368', 'ht11064281', 'ht11067604', 'ht10810178', 'ht11315743', 'ht11061813', 'ht10808218', 'ht10809597', 'ht10808533', 'ht10807949', 'ht11703267', 'ht10809777', 'ht11604914', 'ht10811312', 'ht11703255', 'ht11703244', 'ht11316599', 'ht10296528', 'ht11200413', 'ht11703381', 'ht10327744', 'ht11643732', 'ht10326980', 'ht10756727', 'ht11703316', 'ht11008503', 'ht11466739', 'ht10781971', 'ht10741840', 'ht11703456', 'ht10828919', 'ht11703350', 'ht11703448', 'ht11703402', 'ht11703501', 'ht10303363', 'ht10273213', 'ht11703535', 'ht10250817', 'ht11698432', 'ht11703365', 'ht11703397', 'ht11703523', 'ht11703480', 'ht11703487', 'ht10409074', 'ht11703248', 'ht10772581', 'ht11309062', 'ht10791029', 'ht11703399', 'ht11703188', 'ht11703202', 'ht10338985', 'ht11703371', 'ht10340501', 'ht11703400', 'ht10415070', 'ht10793633', 'ht10412845', 'ht11703071', 'ht10322072', 'ht10806616', 'ht10397584', 'ht11703395', 'ht11085279', 'ht11652590', 'ht11228976', 'ht10846475', 'ht10812871', 'ht11703208', 'ht11703214', 'ht11703231', 'ht10343365', 'ht11424718', 'ht11703197', 'ht11703178', 'ht10770082', 'ht11141740', 'ht11306304', 'ht11308897', 'ht10361292', 'ht11703263', 'ht10348762', 'ht10348050', 'ht10465631', 'ht11703201', 'ht10405205', 'ht10238158', 'ht11309249', 'ht11703341', 'ht11440722', 'ht10742911', 'ht10226057', 'ht11359630', 'ht10693431', 'ht10993088', 'ht11703115', 'ht11703052', 'ht10392745', 'ht11636205', 'ht11703343', 'ht11703347', 'ht11203735', 'ht10833845', 'ht11193897', 'ht10379810', 'ht11703056', 'ht11703057', 'ht10378773', 'ht10377799', 'ht10437795', 'ht10814155', 'ht10815017', 'ht11030936', 'ht10757234', 'ht11703137', 'ht11703164', 'ht11703303', 'ht10737869', 'ht11703462', 'ht10776437', 'ht10797325', 'ht10760929', 'ht11703063', 'ht10797433', 'ht11703156', 'ht10837940', 'ht11609250', 'ht11080945', 'ht10323833', 'ht11030167', 'ht11703101', 'ht11703336', 'ht10361986', 'ht10362538', 'ht11047829', 'ht10434382', 'ht11703089', 'ht11182457', 'ht10617306', 'ht11703473', 'ht11029926', 'ht10771597', 'ht10963444', 'ht11703380', 'ht11166479', 'ht10276365', 'ht10606609', 'ht11301639', 'ht10401222', 'ht11703265', 'ht11703251', 'ht10669051', 'ht10404001', 'ht11703509', 'ht11703511', 'ht11703068', 'ht10801094', 'ht11703078', 'ht11703458', 'ht11703281', 'ht10452507', 'ht11232405', 'ht11703289', 'ht10730795', 'ht11703262', 'ht11703362', 'ht11453484', 'ht11071878', 'ht10756048', 'ht10361272', 'ht10394874', 'ht11703282', 'ht10805141', 'ht10743872', 'ht11703074', 'ht11379794', 'ht11703050', 'ht11332458', 'ht11703382', 'ht10287254', 'ht11703461', 'ht10435443', 'ht11703092', 'ht11703260', 'ht10804527', 'ht10795777', 'ht11703080', 'ht11703277', 'ht11470302', 'ht11111629', 'ht11065241', 'ht10833685', 'ht11068380', 'ht11622837', 'ht11703243', 'ht11185321', 'ht10738627', 'ht10379831', 'ht11703444', 'ht10733082', 'ht11214490', 'ht11382133', 'ht11703286', 'ht11703291', 'ht11311649', 'ht11304679', 'ht11703330', 'ht11260421', 'ht10779464', 'ht10356779', 'ht11703198', 'ht11312107', 'ht11214320', 'ht11703533', 'ht11472567', 'ht10781373', 'ht10064690'
        ]
    }
}, {
    $set: {
        'finished': 0,
        'running': 0,
        'used_times': 0
    }
}, false, true);



