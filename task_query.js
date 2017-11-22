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


db.City_Queue_poi_list_TaskName_city_total_qyer_20171120a.update({}, {$set: {date_index: 0}}, false, true);

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