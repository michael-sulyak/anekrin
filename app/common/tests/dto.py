import dataclasses
import typing


@dataclasses.dataclass
class ActualCall:
    name: str
    args: dataclasses.field(
        default_factory=list,
    )
    kwargs: dataclasses.field(
        default_factory=dict,
    )

    @property
    def has_args(self) -> bool:
        return len(self.args) > 0

    @property
    def has_kwargs(self) -> bool:
        return len(self.kwargs) > 0


class ExpectedCall:
    params: dict[str, typing.Any]

    def __init__(self, **params) -> None:
        self.params = params

    def compare_with(self, call: ActualCall) -> None:
        params = self.params.copy()

        if 'name' in params:
            assert params['name'] == call.name
            del params['name']

        if 'args' in params:
            assert params['args'] == call.args
            del params['args']

        for i in range(5):
            # Simple implementation. We don't need to check a lot of args.
            if f'args__{i}__contains' in params:
                assert params[f'args__{i}__contains'] in call.args[0], \
                    f'{call.args[0]=} doesn\'t contain {params[f"args__{i}__contains"]=}'
                del params[f'args__{i}__contains']

        if 'args__len' in params:
            assert params['args__len'] == len(call.args)
            del params['args__len']

        if 'kwargs' in params:
            assert params['kwargs'] == call.kwargs
            del params['kwargs']

        if 'kwargs__len' in params:
            assert params['kwargs__len'] == len(call.kwargs)
            del params['kwargs__len']

        if 'kwargs__keys' in params:
            assert set(params['kwargs__keys']) == set(call.kwargs)
            del params['kwargs__keys']

        assert not params


class ExpectedCalls:
    expected_calls: tuple[ExpectedCall]

    def __init__(self, *expected_calls: ExpectedCall) -> None:
        self.expected_calls = expected_calls

    def compare_with(self, calls: typing.Sequence[ActualCall]) -> None:
        assert len(self.expected_calls) == len(calls)

        for action, call in zip(self.expected_calls, calls):
            action.compare_with(call)
