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
            assert params['args'] == call.args, f'{params["args"]} != {call.args}'
            del params['args']

        for i in range(len(call.args)):
            key_for_checking = f'args__{i}__contains'
            # Simple implementation. We don't need to check a lot of args.
            if key_for_checking in params:
                assert params[key_for_checking] in call.args[i], \
                    f'{call.args[i]=} doesn\'t contain {params[key_for_checking]=}'
                del params[key_for_checking]

        if 'args__len' in params:
            assert params['args__len'] == len(call.args)
            del params['args__len']

        if 'kwargs' in params:
            assert params['kwargs'] == call.kwargs
            del params['kwargs']

        if 'kwargs__len' in params:
            assert params['kwargs__len'] == len(call.kwargs), f'{params["kwargs__len"]} != len({call.kwargs})'
            del params['kwargs__len']

        if 'kwargs__keys' in params:
            assert set(params['kwargs__keys']) == set(call.kwargs)
            del params['kwargs__keys']

        for key, value in call.kwargs.items():
            key_for_checking = f'kwargs__{key}'
            if key_for_checking in params:
                assert params[key_for_checking] == value, f'{value=} doesn\'t equal to {params[key_for_checking]=}'
                del params[key_for_checking]

        assert not params


class ExpectedCalls:
    expected_calls: tuple[ExpectedCall]

    def __init__(self, *expected_calls: ExpectedCall) -> None:
        self.expected_calls = expected_calls

    def compare_with(self, calls: typing.Sequence[ActualCall]) -> None:
        assert len(self.expected_calls) == len(calls)

        for action, call in zip(self.expected_calls, calls):
            action.compare_with(call)
