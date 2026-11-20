from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class JobStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PENDING: _ClassVar[JobStatus]
    IN_PROGRESS: _ClassVar[JobStatus]
    COMPLETED: _ClassVar[JobStatus]
    FAILED: _ClassVar[JobStatus]

class TaskState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WAIT: _ClassVar[TaskState]
    TASK_READY: _ClassVar[TaskState]
    FINISHED: _ClassVar[TaskState]
PENDING: JobStatus
IN_PROGRESS: JobStatus
COMPLETED: JobStatus
FAILED: JobStatus
WAIT: TaskState
TASK_READY: TaskState
FINISHED: TaskState

class RegisterParticipantRequest(_message.Message):
    __slots__ = ("participant_id",)
    PARTICIPANT_ID_FIELD_NUMBER: _ClassVar[int]
    participant_id: str
    def __init__(self, participant_id: _Optional[str] = ...) -> None: ...

class RegisterParticipantReply(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: _Optional[bool] = ..., message: _Optional[str] = ...) -> None: ...

class TrainingConfig(_message.Message):
    __slots__ = ("num_rounds", "local_epochs", "learning_rate")
    NUM_ROUNDS_FIELD_NUMBER: _ClassVar[int]
    LOCAL_EPOCHS_FIELD_NUMBER: _ClassVar[int]
    LEARNING_RATE_FIELD_NUMBER: _ClassVar[int]
    num_rounds: int
    local_epochs: int
    learning_rate: float
    def __init__(self, num_rounds: _Optional[int] = ..., local_epochs: _Optional[int] = ..., learning_rate: _Optional[float] = ...) -> None: ...

class ModelParameters(_message.Message):
    __slots__ = ("weights",)
    WEIGHTS_FIELD_NUMBER: _ClassVar[int]
    weights: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, weights: _Optional[_Iterable[float]] = ...) -> None: ...

class TrainingTask(_message.Message):
    __slots__ = ("job_id", "round_number", "config", "global_weights")
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    ROUND_NUMBER_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    GLOBAL_WEIGHTS_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    round_number: int
    config: TrainingConfig
    global_weights: ModelParameters
    def __init__(self, job_id: _Optional[str] = ..., round_number: _Optional[int] = ..., config: _Optional[_Union[TrainingConfig, _Mapping]] = ..., global_weights: _Optional[_Union[ModelParameters, _Mapping]] = ...) -> None: ...

class TrainingResult(_message.Message):
    __slots__ = ("job_id", "participant_id", "round_number", "updated_weights", "num_samples", "loss")
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    PARTICIPANT_ID_FIELD_NUMBER: _ClassVar[int]
    ROUND_NUMBER_FIELD_NUMBER: _ClassVar[int]
    UPDATED_WEIGHTS_FIELD_NUMBER: _ClassVar[int]
    NUM_SAMPLES_FIELD_NUMBER: _ClassVar[int]
    LOSS_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    participant_id: str
    round_number: int
    updated_weights: ModelParameters
    num_samples: int
    loss: float
    def __init__(self, job_id: _Optional[str] = ..., participant_id: _Optional[str] = ..., round_number: _Optional[int] = ..., updated_weights: _Optional[_Union[ModelParameters, _Mapping]] = ..., num_samples: _Optional[int] = ..., loss: _Optional[float] = ...) -> None: ...

class CreateJobRequest(_message.Message):
    __slots__ = ("config", "participant_ids")
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    PARTICIPANT_IDS_FIELD_NUMBER: _ClassVar[int]
    config: TrainingConfig
    participant_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, config: _Optional[_Union[TrainingConfig, _Mapping]] = ..., participant_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class CreateJobReply(_message.Message):
    __slots__ = ("job_id",)
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    def __init__(self, job_id: _Optional[str] = ...) -> None: ...

class StartTrainingRequest(_message.Message):
    __slots__ = ("job_id",)
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    def __init__(self, job_id: _Optional[str] = ...) -> None: ...

class StartTrainingReply(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: _Optional[bool] = ..., message: _Optional[str] = ...) -> None: ...

class GetTrainingStatusRequest(_message.Message):
    __slots__ = ("job_id",)
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    def __init__(self, job_id: _Optional[str] = ...) -> None: ...

class TrainingStatus(_message.Message):
    __slots__ = ("job_id", "status", "current_round", "num_rounds", "global_weights")
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CURRENT_ROUND_FIELD_NUMBER: _ClassVar[int]
    NUM_ROUNDS_FIELD_NUMBER: _ClassVar[int]
    GLOBAL_WEIGHTS_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    status: JobStatus
    current_round: int
    num_rounds: int
    global_weights: ModelParameters
    def __init__(self, job_id: _Optional[str] = ..., status: _Optional[_Union[JobStatus, str]] = ..., current_round: _Optional[int] = ..., num_rounds: _Optional[int] = ..., global_weights: _Optional[_Union[ModelParameters, _Mapping]] = ...) -> None: ...

class GetTrainingTaskRequest(_message.Message):
    __slots__ = ("participant_id",)
    PARTICIPANT_ID_FIELD_NUMBER: _ClassVar[int]
    participant_id: str
    def __init__(self, participant_id: _Optional[str] = ...) -> None: ...

class GetTrainingTaskReply(_message.Message):
    __slots__ = ("state", "task")
    STATE_FIELD_NUMBER: _ClassVar[int]
    TASK_FIELD_NUMBER: _ClassVar[int]
    state: TaskState
    task: TrainingTask
    def __init__(self, state: _Optional[_Union[TaskState, str]] = ..., task: _Optional[_Union[TrainingTask, _Mapping]] = ...) -> None: ...

class SubmitTrainingResultReply(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: _Optional[bool] = ..., message: _Optional[str] = ...) -> None: ...
