<?php

namespace App\Http\Controllers;

class StatusController extends Controller
{
    protected $appKeys = [
        'api',
        'filesystem',
        'mysql',
        'redis',
        'rabbitmq',
        'vpn',
        'backup'
    ];

    protected $statusOptions = [
        0 => 'OK',
        1 => 'Failure',
        2 => 'Degraded'
    ];

    /**
     * Show the keys of applications to monitor
     */
    public function getKeys()
    {
        return response()->json($this->appKeys);
    }

    /**
     * Show status for all keys
     */
    public function getDetails()
    {
        $response = [];

        $maxOptions = count($this->statusOptions) - 1;

        foreach ($this->appKeys as $appKey) {
            $statusCode = rand(0, $maxOptions);

            $response[$appKey] = [
                'statusCode' => $statusCode,
                'status' => $this->statusOptions[$statusCode]
            ];
        }

        return response()->json($response);
    }
}
