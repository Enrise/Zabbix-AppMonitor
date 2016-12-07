<?php

namespace App\Http\Controllers;

class StatusController extends Controller
{
    protected $appKeys = [
        'api' => 'critical',
        'filesystem' => 'cricital',
        'mysql' => 'critical',
        'redis' => 'critical',
        'rabbitmq' => 'critical',
        'vpn' => 'high',
        'backup' => 'warning'
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
        #return response()->json($this->appKeys);
        $response = [];

        foreach ($this->appKeys as $appKey => $severity) {
            $response[$appKey] = [
                'severity' => $severity
            ];
        }

        return response()->json($response);
    }

    /**
     * Show status for all keys
     */
    public function getDetails()
    {
        $response = [];

        $maxOptions = count($this->statusOptions) - 1;

        foreach ($this->appKeys as $appKey => $severity) {
            $statusCode = rand(0, $maxOptions);

            $response[$appKey] = [
                'statusCode' => $statusCode,
                'severity' => $severity
            ];
        }

        return response()->json($response);
    }
}
